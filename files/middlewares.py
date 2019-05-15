import aiohttp_jinja2
from aiohttp import web

from .db import users

import jwt


async def handle_404(request):
    return aiohttp_jinja2.render_template('404.html', request, {})


async def handle_500(request):
    return aiohttp_jinja2.render_template('500.html', request, {})


def create_error_middleware(overrides):

    @web.middleware
    async def error_middleware(request, handler):

        try:
            response = await handler(request)

            override = overrides.get(response.status)
            if override:
                return await override(request)

            return response

        except web.HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)

            raise

    return error_middleware


@web.middleware
async def auth_middleware(request, handler):
    request.user = None
    jwt_token = request.headers.get('authorization_jwt', None)
    if jwt_token:
        JWT_SECRET = request.app['config']['jwt']['secret']
        JWT_ALGORITHM = request.app['config']['jwt']['algo']
        try:
            payload = jwt.decode(jwt_token, JWT_SECRET,
                                    algorithms=[JWT_ALGORITHM])
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return web.json_response({'message': 'Token is invalid'}, status=400)

        async with request.app['db'].acquire() as conn:
            query = users.select().where(users.c.id == payload['user_id'])
            ret = await conn.execute(query)
            user_record = await ret.fetchone()
            request.user = user_record
    return await handler(request)


def setup_middlewares(app):
    error_middleware = create_error_middleware({
        404: handle_404,
        500: handle_500
    })
    app.middlewares.append(error_middleware)
    app.middlewares.append(auth_middleware)


def login_required(func):
    async def wrapper(request):
        if not request.user:
            return web.json_response({'message': 'Auth required'}, status=web.HTTPUnauthorized.status_code)
        return await func(request)
    return wrapper