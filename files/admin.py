import aiohttp_admin
import aiohttp_security

from aiohttp_admin.contrib import models, Schema
from aiohttp_admin.backends.sa import PGResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy

from files.db_tables import users, file


schema = Schema()


def setup_admin(app, pg):
    admin = aiohttp_admin._setup(
        app,
        title='Files admin',
        schema=schema,
        db=pg,
    )

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username=app['config']['aiohttp-admin']['user'],
                                  password=app['config']['aiohttp-admin']['password'])
    aiohttp_security.setup(admin, ident_policy, auth_policy)

    app.add_subapp('/admin', admin)


@schema.register
class Users(models.ModelAdmin):
    fields = ('id', 'username', 'email', 'passwd')

    class Meta:
        resource_type = PGResource
        table = users


@schema.register
class File(models.ModelAdmin):
    fields = ('id', 'slug', 'filename', 'pub_date', 'user_id')

    class Meta:
        resource_type = PGResource
        table = file
