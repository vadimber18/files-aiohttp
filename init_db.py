import json
from datetime import datetime, timedelta

from sqlalchemy import create_engine, MetaData

from files.settings import BASE_DIR, CONFIG, TEST_CONFIG

from files.db_tables import users, file


DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"

USER_CONFIG = CONFIG
USER_DB_URL = DSN.format(**USER_CONFIG['postgres'])
user_engine = create_engine(USER_DB_URL)
admin_engine = create_engine(USER_DB_URL, isolation_level='AUTOCOMMIT')

TEST_CONFIG = TEST_CONFIG
TEST_DB_URL = DSN.format(**TEST_CONFIG['postgres'])
test_engine = create_engine(TEST_DB_URL)

FIXTURES_PATH = BASE_DIR / 'tests' / 'json_fixtures'


def setup_db(config):

    db_name = config['database']
    db_user = config['user']
    db_pass = config['password']

    conn = admin_engine.connect()
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.execute("CREATE USER %s WITH PASSWORD '%s'" % (db_user, db_pass))
    conn.execute("CREATE DATABASE %s ENCODING 'UTF8'" % db_name)
    conn.execute("GRANT ALL PRIVILEGES ON DATABASE %s TO %s" %
                 (db_name, db_user))
    conn.close()


def teardown_db(config):

    db_name = config['database']
    db_user = config['user']

    conn = admin_engine.connect()
    conn.execute("""
      SELECT pg_terminate_backend(pg_stat_activity.pid)
      FROM pg_stat_activity
      WHERE pg_stat_activity.datname = '%s'
        AND pid <> pg_backend_pid();""" % db_name)
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.close()

def create_tables(engine=test_engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[users, file])


def drop_tables(engine=test_engine):
    meta = MetaData()
    meta.drop_all(bind=engine, tables=[users, file])


def insert_from_fixtures(conn):
    fixture_list = ['users.json', 'file.json']
    for filename in fixture_list:
        with open(FIXTURES_PATH / filename) as f:
            data = json.load(f)
        for record in data:
            if filename == 'file.json':
                if record['pub_date']:
                    record['pub_date'] = datetime.strptime(record['pub_date'], '%Y-%m-%d')
            conn.execute(eval(filename.split('.')[0]).insert(), record)


def sample_data(engine=test_engine):
    conn = engine.connect()

    # we can put here sample data for both engines
    # TODO temporary we add fixtures data for ordinary version
    #insert_from_fixtures(conn)

    if engine==test_engine:
        insert_from_fixtures(conn)

    conn.close()


if __name__ == '__main__':

    #setup_db(USER_CONFIG['postgres'])
    create_tables(engine=user_engine)
    sample_data(engine=user_engine)
    # drop_tables()
    # teardown_db(config)
