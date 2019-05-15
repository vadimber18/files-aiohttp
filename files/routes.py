import pathlib

from .views import register, login, files, file_detail, file_upload, file_download

import aiohttp_cors

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    # auth endpoints
    app.router.add_route('POST', '/api/register', register)
    app.router.add_route('POST', '/api/login', login)

    # "viewset" endpoints
    app.router.add_route('GET', '/api/files', files)
    app.router.add_route('GET', '/api/files/{file_id}', file_detail)

    # "viewset actions" endpoints
    app.router.add_route('POST', '/api/files/upload', file_upload)
    app.router.add_route('GET', '/api/files/download/{file_id}', file_download)

    #if app['config']['debug']:
    #    setup_static_routes(app)


def setup_cors(app):
    # swagger server
    cors = aiohttp_cors.setup(app, defaults={
        "http://127.0.0.1:8000": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)


def setup_static_routes(app):
    app.router.add_static('/static/',
                          path=PROJECT_ROOT / 'static',
                          name='static')