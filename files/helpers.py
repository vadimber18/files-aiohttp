from datetime import datetime

from .db_tables import file


def prepare_filter_parameters(query):
    filters = {}
    if 'user' in query:
        assert [int(i) for i in query['user'].split(',')]
        filters.update({'user': query['user']})
    date_filter = {}
    if 'from' in query:
        assert datetime.strptime(query['from'], '%d-%m-%Y')
        date_filter.update({'from': query['from']})
        filters.update({'date': date_filter})
    if 'to' in query:
        assert datetime.strptime(query['to'], '%d-%m-%Y')
        date_filter.update({'to': query['to']})
        filters.update({'date': date_filter})
    pagination = {}
    if 'limit' in query:
        assert int(query['limit']) > 0
        pagination.update({'limit': query['limit']})
    if 'offset' in query:
        assert int(query['offset']) > 0
        pagination.update({'offset': query['offset']})
    return pagination, filters


def prepare_files_response(files, count, rel_url):
    if not len(rel_url.query_string):
        next_request = str(rel_url) + '?offset=20'
    else:
        if not 'offset' in rel_url.query:
            next_request = str(rel_url) + '&offset=20'
        else:
            value = int(rel_url.query['offset'])
            next_request = str(rel_url).replace(f'offset={str(value)}', f'offset={str(value + 20)}')

    return {'count': count, 'next': next_request,'results': files}


def make_where_list_files(filters, many=True):
    where_list = []
    if not filters:
        return where_list
    if not many:
        if filters.isdigit(): # file_id
            where_list.append(file.c.id==filters) # we pass file_id through
        else:
            where_list.append(file.c.slug==filters)
        return where_list
    if 'user' in filters:
        where_list.append(file.c.user_id.in_([int(usr) for usr in filters['user'].split(',')]))
    if 'date' in filters:
        if 'from' in filters['date']:
            from_date = datetime.strptime(filters['date']['from'], '%d-%m-%Y')
            where_list.append(file.c.pub_date >= from_date)
        if 'to' in filters['date']:
            to_date = datetime.strptime(filters['date']['to'], '%d-%m-%Y')
            where_list.append(file.c.pub_date <= to_date)
    return where_list
