from passlib.hash import sha256_crypt

from .exceptions import BadRequest
from .db_tables import file, users


async def validate_file(conn, file_id):
    cursor = await conn.execute(
        file.select()
            .where(file.c.id == file_id))
    file_record = await cursor.fetchone()
    if not file_record:
        raise BadRequest('No file with such id')


async def validate_login(conn, data):
    required_fields = ['username', 'password']
    if any(field not in data for field in required_fields):
        raise BadRequest('Request data does not match required fields')

    return await check_credentials(conn, data['username'], data['password'])


async def check_credentials(conn, username, password):
    query = users.select().where(users.c.username == username)
    ret = await conn.execute(query)
    user_record = await ret.fetchone()
    if user_record:
        hash = user_record['passwd']
        result = sha256_crypt.verify(password, hash)
        if result:
            return user_record
    raise BadRequest('Wrong credentials')


async def validate_register(conn, data):
    required_fields = ['username', 'password', 'email']

    if any(field not in data for field in required_fields):
        raise BadRequest('Request data does not match required fields')

    username = data['username']

    cursor = await conn.execute(
            users.select()
            .where(users.c.username == username))
    user_record = await cursor.fetchone()
    if user_record:
        raise BadRequest('User with this username already exists')

    email = data['email']

    if '@' not in email:
        raise BadRequest('Wrong email format')

    cursor = await conn.execute(
            users.select()
            .where(users.c.email == email))
    user_record = await cursor.fetchone()
    if user_record:
        raise BadRequest('User with this email already exists')
