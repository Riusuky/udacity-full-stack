from redis import Redis

from oauth2client import client, crypt

import time, sys
from functools import update_wrapper
from flask import request, g, make_response
from flask import Flask, jsonify, render_template

from models import User, Category, Image, Item, Response, engine

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import DataError
from sqlalchemy.exc import InternalError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import InvalidRequestError

from flask import session as login_session
import random
import string

redis = Redis()

db_session = sessionmaker()
db_session.configure(bind=engine)

session = db_session()

app = Flask(__name__)

def generate_state():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))


def requires_authentication(f):
    def decorator(*args, **kwargs):
        if 'userid' not in login_session:
            return (jsonify({'data':'Request requires authentication','error':'401'}),401)

        return f(*args, **kwargs)

    return update_wrapper(decorator, f)


def check_authorization(userid):
    if 'userid' in login_session:
        return login_session['userid'] == userid

    return False

def get_user(email):
    try:
        return session.query(User).filter(
            User.email == email).one()
    except NoResultFound:
        return None
    except:
        return None

def add_user(email, name):
    try:
        new_user = User(email = email, name = name)

        session.add(new_user)
        session.commit()

        return new_user
    except IntegrityError:
        session.rollback()
        return None
    except InvalidRequestError as e:
        print(e)
        return None
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None

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

@requires_authentication
def add_category(name):
    owner_id = login_session['userid']

    try:
        session.add(Category(name = name, owner_id = owner_id))
        session.commit()

        return Response('Success')
    except IntegrityError:
        session.rollback()
        return Response(
            error = 'Invalid new category parameters. '
            '(name: {}, owner_id: {})'.format(name, owner_id))
    except InvalidRequestError as e:
        print(e)
        return Response(error = 'Failed to add new category')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(error = 'Failed to add new category')

@requires_authentication
def delete_category(id):
    try:
        category = session.query(Category).filter(Category.id == id).one()

        if not check_authorization(category.owner_id):
            return (jsonify({'data':'Permission denied','error':'401'}),401)

        session.delete(category)
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

@requires_authentication
def add_item(name, category_id, description = None, image_id = None):
    owner_id = login_session['userid']

    try:
        session.add(
            Item(
                name = name,
                description = description,
                owner_id = owner_id,
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
                        'owner_id: {}'
                        'image_id: {})'
                        .format(name,
                            description,
                            category_id,
                            owner_id,
                            image_id))
    except InvalidRequestError as e:
        print(e)
        return Response(error = 'Failed to add new item')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(error = 'Failed to add new item')

@requires_authentication
def update_item(id, name = None, category_id = None, description = None, image_id = None):
    try:
        target = session.query(Item).filter(Item.id == id).one()
    except NoResultFound:
        return Response(error = 'No result found')
    except:
        return Response(error = 'Unknown error')
    else:
        if not check_authorization(target.owner_id):
            return (jsonify({'data':'Permission denied','error':'401'}),401)

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

@requires_authentication
def delete_item(id):
    try:
        target = session.query(Item).filter(Item.id == id).one()

        if not check_authorization(target.owner_id):
            return (jsonify({'data':'Permission denied','error':'401'}),401)

        session.delete(target)
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
    state =  generate_state()
    print(login_session['state'])
    print(state)
    login_session['state'] = state

    return render_template('index.html', STATE=state)

@app.route('/category')
@ratelimit(limit=30, per=60 * 1)
def page_category():
    state =  generate_state()
    login_session['state'] = state

    return render_template('index.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
@ratelimit(limit=30, per=60 * 1)
def gconnect():
    if request.args.get('state') != login_session['state']:
        return (jsonify({'data':'Invalid state parameter','error':'401'}),401)

    try:
        idinfo = client.verify_id_token(request.data, '1014623565180-lm2sl4gftjv5r8jhgikg0ti9lcldol8c.apps.googleusercontent.com')

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError:
        return (jsonify({'data':'Invalid authentication issuer','error':'401'}),401)

    print(idinfo)

    user = get_user(idinfo['email'])

    if user is None:
        user = add_user(idinfo['email'], idinfo['name'])

        if user is None:
            return (jsonify({'data':'Internal Error','error':'500'}),500)

    login_session['userid'] = user.id

    return jsonify(Response({'user_name': idinfo['name'], 'user_picture': idinfo['picture']}).tojson())

@app.route('/gdisconnect', methods=['POST'])
@ratelimit(limit=30, per=60 * 1)
@requires_authentication
def gdisconnect():
    if request.args.get('state') != login_session['state']:
        return (jsonify({'data':'Invalid state parameter','error':'401'}),401)
        
    del login_session['userid']

    return jsonify(Response('User disconnected successfully').tojson())

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
    app.secret_key = 'i3Ldm4dv8c9sBsc45A3vx6sO3plsn'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
