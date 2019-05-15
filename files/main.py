import logging
import sys

from aiohttp import web

from files.db import close_pg, init_pg
from files.middlewares import setup_middlewares
from files.routes import setup_routes, setup_cors
from files.settings import CONFIG, TEST_CONFIG
from files.admin import setup_admin


async def init_app(testing=False):
    app = web.Application()

    app['config'] = TEST_CONFIG if testing else CONFIG

    # create db connection on startup, shutdown on exit
    pg = await init_pg(app)
    setup_admin(app, pg)

    app.on_cleanup.append(close_pg)

    # setup views and routes
    setup_routes(app)
    # setup cors for swagger
    setup_cors(app)

    setup_middlewares(app)

    return app


def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    app = init_app(argv)

    config = CONFIG
    web.run_app(app,
                host=config['host'],
                port=config['port'])


if __name__ == '__main__':
    main(sys.argv[1:])
