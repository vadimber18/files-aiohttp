import json

from faker import Faker


def json_str_dumps(thing):
    ''' otherwise got problems with serialize date things '''
    return json.dumps(thing, default=str)


def get_random_name():
    fake = Faker()
    return fake.name()
