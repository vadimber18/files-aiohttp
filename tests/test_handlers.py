import hashlib
from datetime import datetime

from files.db_tables import file
import sqlalchemy as sa


async def test_register(cli, tables_and_data):
    response = await cli.post(
        '/api/register',
        json={'username':'test_user', 'email': 'test@test.test'}
    )
    assert response.status == 400 # no password

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 400 # no email

    response = await cli.post(
        '/api/register',
        json={'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 400 # no username

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'testtest.test'}
    )
    assert response.status == 400 # bad email format

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test_two@test.test'}
    )
    assert response.status == 400 # user with this username already exists

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user_two', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 400 # user with this email already exists

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user_two', 'password': 'qwerty', 'email': 'test_two@test.test'}
    )
    assert response.status == 200


async def test_login(cli, tables_and_data):
    response = await cli.post(
        '/api/login',
        json={'password': 'qwerty'}
    )
    assert response.status == 400 # no username

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user'}
    )
    assert response.status == 400 # no password

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 400 # no username in db

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwertyq'}
    )
    assert response.status == 400 # bad password

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert 'token' in await response.text()
    assert response.status == 200


async def test_files(cli, tables_and_data):

    # w/o authorization
    file_fields = ['file_id', 'file_slug', 'file_filename', 'file_pub_date', 'file_user_id',
                   'users_username', 'users_email']

    response = await cli.get('/api/files')
    assert response.status == 200
    response_data = await response.json()

    # checks fields in response data
    assert 'count' in response_data
    assert 'next' in response_data
    assert 'results' in response_data

    file_objects = response_data['results']
    assert len(response_data['results']) <= 20 # default limit
    assert response_data['next'] == '/api/files?offset=20'

    # checks fields in every file object
    for file_object in file_objects:
        for field in file_fields:
            assert field in file_object
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(sa.select([sa.func.count()])
                                    .select_from(
                                        file))
        count_record = await cursor.fetchone()
        assert count_record[0] == response_data['count']

    # check filters
    # user filter
    response = await cli.get('/api/files?user=1')
    assert response.status == 200
    response_data = await response.json()
    for one_file in response_data['results']:
        assert one_file['file_user_id'] == 1

    response = await cli.get('/api/files?user=1,2')
    assert response.status == 200
    response_data = await response.json()
    for one_file in response_data['results']:
        assert one_file['file_user_id'] in [1, 2]

    # date filter
    response = await cli.get('/api/files?from=1-1-2018')
    assert response.status == 200
    response_data = await response.json()
    test_date = datetime(year=2018, month=1, day=1).date()
    for one_file in response_data['results']:
        one_file_date = datetime.strptime(one_file['file_pub_date'], '%Y-%m-%d').date()
        assert one_file_date >= test_date

    response = await cli.get('/api/files?to=1-12-2018')
    assert response.status == 200
    response_data = await response.json()
    test_date = datetime(year=2018, month=12, day=1).date()
    for one_file in response_data['results']:
        one_file_date = datetime.strptime(one_file['file_pub_date'], '%Y-%m-%d').date()
        assert one_file_date <= test_date

    response = await cli.get('/api/files?to=1-1-2018&from=1-1-2017')
    assert response.status == 200
    response_data = await response.json()
    test_date_to = datetime(year=2018, month=1, day=1).date()
    test_date_from = datetime(year=2017, month=1, day=1).date()
    for one_file in response_data['results']:
        one_file_date = datetime.strptime(one_file['file_pub_date'], '%Y-%m-%d').date()
        assert one_file_date <= test_date_to
        assert one_file_date >= test_date_from

    # pagination
    response = await cli.get('/api/files?limit=40')
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) <= 40

    response = await cli.get('/api/files?limit=40&offset=20')
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) <= 40

    # multiple filters
    response = await cli.get('/api/files?to=1-12-2018&from=1-1-2017&user=2&limit=5&offset=5')
    assert response.status == 200
    response_data = await response.json()
    test_date_to = datetime(year=2018, month=12, day=1).date()
    test_date_from = datetime(year=2017, month=1, day=1).date()
    for one_file in response_data['results']:
        one_file_date = datetime.strptime(one_file['file_pub_date'], '%Y-%m-%d').date()
        assert one_file_date <= test_date_to
        assert one_file_date >= test_date_from
        assert one_file['file_users_id'] == 2
    assert len(response_data['results']) <= 5


async def test_file_detail(cli, tables_and_data):

    # w/o authorization
    file_fields = ['file_id', 'file_slug', 'file_filename', 'file_pub_date', 'file_user_id',
                   'users_username', 'users_email']

    # both for id and slug
    response = await cli.get('/api/files/abc')
    assert response.status == 200
    response = await cli.get('/api/files/340')
    assert response.status == 200
    response_data = await response.json()
    # checks fields in file object
    for field in file_fields:
        assert field in response_data

    response = await cli.get('/api/files/1')
    assert response.status == 400 # bad file id


async def test_file_download_detail(cli, tables_and_data):

    # w/o authorization
    response = await cli.get('/api/files/download/abc')
    assert response.status == 401 # no authorization

    # /w authorization
    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200
    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.get('/api/files/download/abc', headers = {'authorization_jwt': token})
    assert response.status == 200
    response = await cli.get('/api/files/download/340', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()

    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(file.select()
                                    .where(file.c.id==340))
        file_record = await cursor.fetchone()
        # we know that response_data is full path, so we get only filename from it
        assert response_data.split('/')[-1] == dict(file_record)['filename']

    response = await cli.get('/api/files/1', headers = {'authorization_jwt': token})
    assert response.status == 400 # bad file id


async def test_file_upload_detail(cli, tables_and_data):

    # w/o authorization
    response = await cli.post('/api/files/upload')
    assert response.status == 401 # no authorization

    # /w authorization
    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200
    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']


    test_filename = 'testfile.txt'
    with open(test_filename, 'w+') as f:
        f.write('some text')

    # aiohttp will stream file object to the server automatically
    files = {'file': open(test_filename, 'rb')}
    response = await cli.post('/api/files/upload', headers = {'authorization_jwt': token}, data=files)
    assert response.status == 200
    response_data = await response.json()
    assert response_data == hashlib.sha1(test_filename.encode()).hexdigest()

    # we also make sure collisions will not happen
    # stream thing closed file handler so we need to open file again
    files = {'file': open(test_filename, 'rb')}
    response = await cli.post('/api/files/upload', headers = {'authorization_jwt': token}, data=files)
    assert response.status == 200
    response_data = await response.json()
    test_filename += '-1'
    assert response_data == hashlib.sha1(test_filename.encode()).hexdigest()