from redis import Redis


import time, sys
from functools import update_wrapper
from flask import request, g
from flask import Flask, jsonify

from models import Category, Image, Item, Response, engine

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import DataError, InternalError, IntegrityError, InvalidRequestError

redis = Redis()

db_session = sessionmaker()
db_session.configure(bind=engine)

session = db_session()

app = Flask(__name__)

def get_categories(id = None):
    if id is not None:
        try:
            response = Response(session.query(Category).filter(
                Category.id == id).one().tojson())
        except NoResultFound:
            response = Response(error = 'No result found')
        except:
            response = Response(error = 'Unknown error')

        return response
    else:
        category_list = []

        for category in session.query(Category).all():
            category_list.append(category.tojson())

        return Response(category_list) if len(category_list) > 0 \
            else Response(error = 'No result found')

def add_category(name):
    try:
        session.add(Category(name = name))
        session.commit()

        return Response('Success')
    except IntegrityError:
        session.rollback()
        return Response(
            error = 'Invalid new category name. (name: {})'.format(name))
    except InvalidRequestError as e:
        print(e)
        return Response(error = 'Failed to add new category')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(error = 'Failed to add new category')


def delete_category(id):
    try:
        session.delete(session.query(Category).filter(Category.id == id).one())
        session.commit()

        return Response('Success')
    except DataError:
        return Response(error = 'Category id is not an integer')
    except NoResultFound:
        return Response(
            error = 'There is no category that corresponds '
                    'to the specified id. (id: {})'.format(id))
    except InternalError as e:
        print(e)
        return Response(
            error = 'Failed to delete category with id: {}'.format(id))
    except IntegrityError as e:
        print(e)
        session.rollback()
        return Response(
            error = 'Failed to delete category with id: {}'.format(id))
    except InvalidRequestError as e:
        print(e)
        return Response(
            error = 'Failed to delete category with id: {}'.format(id))
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error = 'Failed to delete category with id: {}'.format(id))


def get_items(id = None):
    if id is not None:
        try:
            response = Response(session.query(Item).filter(
                Item.id == id).one().tojson())
        except NoResultFound:
            response = Response(error = 'No result found')
        except:
            response = Response(error = 'Unknown error')

        return response
    else:
        item_list = []

        for item in session.query(Item).all():
            item_list.append(item.tojson())

        return Response(item_list) if len(item_list) > 0\
            else Response(error = 'No result found')

def add_item(name, category_id, description = None, image_id = None):
    try:
        session.add(
            Item(
                name = name,
                description = description,
                category_id = category_id,
                image_id = image_id))
        session.commit()

        return Response('Success')
    except IntegrityError as e:
        print(e)
        session.rollback()
        return Response(error = 'Invalid new item parameters. '
                        '(name: {}, '
                        'description: {}, '
                        'category_id: {}, '
                        'image_id: {})'
                        .format(name, description, category_id, image_id))
    except InvalidRequestError as e:
        print(e)
        return Response(error = 'Failed to add new item')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(error = 'Failed to add new item')

def update_item(id, name = None, category_id = None, description = None, image_id = None):
    try:
        target = session.query(Item).filter(Item.id == id).one()
    except NoResultFound:
        return Response(error = 'No result found')
    except:
        return Response(error = 'Unknown error')
    else:
        updated = False

        if name and (target.name != name):
            target.name = name
            updated = True

        if category_id and (target.category_id != category_id):
            target.category_id = category_id
            updated = True

        if description and (target.description != description):
            target.description = description
            updated = True

        if image_id and (target.image_id != image_id):
            target.image_id = image_id
            updated = True

        if updated:
            target.created_on = func.now()

            try:
                session.add(target)
                session.commit()

                return Response('Success')
            except IntegrityError as e:
                print(e)
                session.rollback()
                return Response(error = 'Invalid new item parameters. '
                                '(name: {}, '
                                'description: {}, '
                                'category_id: {}, '
                                'image_id: {})'
                                .format(name, description, category_id, image_id))
            except InvalidRequestError as e:
                print(e)
                return Response(error = 'Failed to update item')
            except:
                print("Unexpected error:", sys.exc_info()[0])
                return Response(error = 'Failed to update item')
        else:
            return Response('Item has not changed')


def delete_item(id):
    try:
        session.delete(session.query(Item).filter(Item.id == id).one())
        session.commit()

        return Response('Success')
    except DataError:
        return Response(error = 'Item id is not an integer')
    except NoResultFound:
        return Response(
            error = 'There is no item that corresponds '
                    'to the specified id. (id: {})'.format(id))
    except InternalError as e:
        print(e)
        return Response(
            error = 'Failed to delete item with id: {}'.format(id))
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error = 'Failed to delete item with id: {}'.format(id))


class RateLimit(object):
    expiration_window = 10

    def __init__(self, key_prefix, limit, per, send_x_headers):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        self.send_x_headers = send_x_headers
        p = redis.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)

def get_view_rate_limit():
    return getattr(g, '_view_rate_limit', None)

def on_over_limit(limit):
    return (jsonify({'data':'You hit the rate limit','error':'429'}),429)

def ratelimit(limit, per=300, send_x_headers=True,
              over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    def decorator(f):
        def rate_limited(*args, **kwargs):
            key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
            rlimit = RateLimit(key, limit, per, send_x_headers)
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator


@app.after_request
def inject_x_rate_headers(response):
    limit = get_view_rate_limit()
    if limit and limit.send_x_headers:
        h = response.headers
        h.add('X-RateLimit-Remaining', str(limit.remaining))
        h.add('X-RateLimit-Limit', str(limit.limit))
        h.add('X-RateLimit-Reset', str(limit.reset))
    return response

@app.route('/')
@ratelimit(limit=30, per=60 * 1)
def index():
    return 'Index'

@app.route('/category')
@ratelimit(limit=30, per=60 * 1)
def page_category():
    return 'Category'

@app.route('/api/category',
    defaults={'category': None},
    methods=['GET', 'POST', 'DELETE'])
@app.route('/api/category/<int:category>',
    methods=['GET', 'DELETE'])
@ratelimit(limit=10, per=60 * 1)
def api_category(category):
    if request.method == 'GET':
        return jsonify(get_categories(category).tojson())

    elif request.method == 'POST':
        if 'name' in request.json:
            return jsonify(add_category(name = request.json['name']).tojson())
        else:
            return jsonify(
                Response(error = 'Missing "name" parameter').tojson())

    elif request.method == 'DELETE':
        if category:
            return jsonify(delete_category(category).tojson())
        elif 'id' in request.json:
            return jsonify(delete_category(request.json['id']).tojson())
        else:
            return jsonify(
                Response(error = 'Missing "id" parameter').tojson())
    else:
        return jsonify(
            Response(error = 'Method is not yet implemented').tojson())

@app.route('/api/item',
    defaults={'item': None},
    methods=['GET', 'POST', 'DELETE'])
@app.route('/api/item/<int:item>',
    methods=['GET', 'DELETE', 'PATCH'])
@ratelimit(limit=10, per=60 * 1)
def api_item(item):
    if request.method == 'GET':
        return jsonify(get_items(item).tojson())

    elif request.method == 'POST':
        if ('name' in request.json) and ('category_id' in request.json):
            return jsonify(add_item(**request.json).tojson())
        else:
            return jsonify(
                Response(
                    error = 'Missing "name" '
                            'or "category_id" parameters').tojson())

    elif request.method == 'DELETE':
        if item:
            return jsonify(delete_item(item).tojson())
        elif 'id' in request.json:
            return jsonify(delete_item(request.json['id']).tojson())
        else:
            return jsonify(
                Response(error = 'Missing "id" parameter').tojson())

    elif request.method == 'PATCH':
        return jsonify(update_item(item, **request.json).tojson())
    else:
        return jsonify(
            Response(error = 'Method is not yet implemented').tojson())

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
