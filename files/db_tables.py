from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date
)


meta = MetaData()


users = Table(
    'users', meta,

    Column('id', Integer, primary_key=True),
    Column('username', String(64), nullable=False),
    Column('email', String(120), nullable=False, unique=True),
    Column('passwd', String(128), nullable=False)
)

file = Table(
    'file', meta,

    Column('id', Integer, primary_key=True),
    Column('slug', String(120), index=True, unique=True),
    Column('filename', String(120), nullable=False),
    Column('pub_date', Date),
    # file owner
    Column('user_id',
           Integer,
           ForeignKey('users.id', ondelete='CASCADE'))
)
