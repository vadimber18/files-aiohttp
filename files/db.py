import hashlib
from datetime import datetime, timedelta

import aiopg.sa

import jwt
import sqlalchemy as sa
from passlib.hash import sha256_crypt

from .helpers import make_where_list_files
from .exceptions import RecordNotFound
from .validators import validate_login, validate_register
from .db_tables import (
    users, file
)


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine
    return engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()


async def generate_filename(dbengine, filename):
    async with dbengine.acquire() as conn:
        cursor = await conn.execute(file.select()
                                    .where(file.c.filename == filename))
        record = await cursor.fetchone()
        cursor.close()
        if record is not None:
            suffix = 0
            while record is not None:
                suffix += 1
                filename = f'{filename}-{str(suffix)}'
                cursor = await conn.execute(file.select()
                                            .where(file.c.filename == filename))
                record = await cursor.fetchone()
                cursor.close()
        return filename


async def save_file(dbengine, filename, usr):
    async with dbengine.acquire() as conn:
        slug = await generate_slug(conn, filename)
        cursor = await conn.execute(
            file.insert()
                .values(slug=slug,
                        filename=filename,
                        pub_date=datetime.now().date(),
                        user_id=usr['id'])
                .returning(file.c.slug)
        )
        file_record = await cursor.fetchone()

        if not file_record:
            raise RecordNotFound("Error while creating new file record")

        return file_record


async def generate_slug(conn, filename):
    slug = hashlib.sha1(filename.encode()).hexdigest() # could use hash() here, but we want slug to be string
    # actually, we dont care about collisions cause we already generated unique filename
    return slug


async def get_file_list(dbengine, pagination=None, filters=None, many=True):
    if pagination:
        limit = pagination['limit'] if 'limit' in pagination else 20
        offset = pagination['offset'] if 'offset' in pagination else 0
    else:
        limit, offset = 20, 0
    where_list = make_where_list_files(filters, many)

    async with dbengine.acquire() as conn:
        files = await get_pure_file_list(conn, limit, offset, where_list, many)
        if many:
            # fetch count for full filtered file list
            count = await get_file_list_count(conn, where_list)
            return files, count
        return files[0]


async def get_pure_file_list(conn, limit, offset, where_list, many):
    ''' selects related user for file '''

    query = sa.select([file, users.c.username, users.c.email], use_labels=True).\
        select_from(
            file.join(users, users.c.id == file.c.user_id)
        ).group_by(file.c.id, users.c.id)


    for where in where_list:
        query = query.where(where)

    if not many:
        cursor = await conn.execute(query)
        file_record = await cursor.fetchone()
        if not file_record:
            raise RecordNotFound('No file with such id')
        rec = dict(file_record)
        return [rec]

    query = query.limit(limit).offset(offset)

    cursor = await conn.execute(query)
    file_records = await cursor.fetchall()
    files = [dict(q) for q in file_records]


    return files


async def get_file_list_count(conn, where_list):
    query = sa.select([sa.func.count()]).select_from(file)
    for where in where_list:
        query = query.where(where)
    cursor = await conn.execute(query)
    count_record = await cursor.fetchone()
    return count_record[0]


async def login(dbengine, data, jwt_config):
    async with dbengine.acquire() as conn:
        user = await validate_login(conn, data)
        JWT_SECRET = jwt_config['secret']
        JWT_ALGORITHM = jwt_config['algo']
        JWT_EXP_DELTA_SECONDS = jwt_config['exp']
        payload = {
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        return jwt_token


async def register(dbengine, data):
    async with dbengine.acquire() as conn:
        await validate_register(conn, data)
        password_hash = sha256_crypt.hash(data['password'])
        query = users.insert().values(username=data['username'], passwd=password_hash, email=data['email']).returning(users.c.id)
        cursor = await conn.execute(query)
        user_record = cursor.fetchone()
        if not user_record:
            raise RecordNotFound('There were an error with creating new user')
