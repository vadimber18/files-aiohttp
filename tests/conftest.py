import pytest

from files.main import init_app
from files.settings import TEST_CONFIG
from init_db import (
    setup_db,
    teardown_db,
    create_tables,
    sample_data,
    drop_tables
)


@pytest.fixture
async def cli(loop, aiohttp_client, db):
    app = await init_app(testing=True)
    return await aiohttp_client(app)


@pytest.fixture(scope='module')
def db():
    setup_db(TEST_CONFIG['postgres'])
    yield
    teardown_db(TEST_CONFIG['postgres'])


@pytest.fixture
def tables_and_data():
    create_tables()
    sample_data()
    yield
    drop_tables()
