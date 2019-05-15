import os

from aiohttp import web

from . import db
from .helpers import prepare_filter_parameters, prepare_files_response
from .utils import json_str_dumps
from .middlewares import login_required


async def register(request):
    data = await request.json()
    try:
        await db.register(request.app['db'], data)
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    return web.json_response({'success': True})


async def login(request):
    data = await request.json()
    try:
        token = await db.login(request.app['db'], data, request.app['config']['jwt'])
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)

    return web.json_response({'token': token.decode('utf-8')})


async def files(request):
    try:
        pagination, filters = prepare_filter_parameters(request.query)
        files, count = await db.get_file_list(request.app['db'], pagination, filters)
        response = prepare_files_response(files, count, request.rel_url)
        return web.json_response(response, dumps=json_str_dumps)
    except Exception as e:
        #import traceback
        #print(traceback.format_tb(e.__traceback__))
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


async def file_detail(request):
    ''' detail view '''
    file_id = request.match_info['file_id'] # we can get both file_id or slug
    try:
        file = await db.get_file_list(request.app['db'],
                                          pagination=None,
                                          filters=file_id,
                                          many=False)
        return web.json_response(file, dumps=json_str_dumps)
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def file_upload(request):
    try:
        reader = await request.multipart()

        field = await reader.next()
        assert field.name == 'file' #TODO validate
        filename = field.filename
        filename = await db.generate_filename(request.app['db'], filename)

        with open(os.path.join(request.app['config']['upload_path'], filename), 'wb') as f:
            while True:
                chunk = await field.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                f.write(chunk)

        file = await db.save_file(request.app['db'], filename, request.user)

        return web.json_response(file['slug'], dumps=json_str_dumps)

    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def file_download(request):
    file_id = request.match_info['file_id'] # we can get both file_id or slug
    try:
        file = await db.get_file_list(request.app['db'],
                                          pagination=None,
                                          filters=file_id,
                                          many=False)
        file_path = os.path.join(request.app['config']['upload_path'], file['file_filename'])
        return web.json_response(file_path, dumps=json_str_dumps)
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def bad_file_download(request):
    # we dont like this due to getting all the file in memory
    file_id = request.match_info['file_id']
    try:
        file = await db.get_file_list(request.app['db'],
                                          pagination=None,
                                          filters=file_id,
                                          many=False)

        with open(os.path.join(request.app['config']['upload_path'], file['file_filename']), 'r') as f:
            content = f.read()
            return web.json_response({'content': content}, dumps=json_str_dumps)

    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
