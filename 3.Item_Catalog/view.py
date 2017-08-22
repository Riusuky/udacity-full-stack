from redis import Redis

from oauth2client import client, crypt

import time
import sys
import os
from functools import update_wrapper
from flask import request, g, make_response
from flask import Flask, jsonify, render_template

from models import User, Category, Image, Item, engine
from models import uploaded_images

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import DataError
from sqlalchemy.exc import InternalError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import InvalidRequestError

from flask import session as login_session

from flask_uploads import configure_uploads, UploadNotAllowed

import random
import string

redis = Redis()

db_session = sessionmaker()
db_session.configure(bind=engine)

session = db_session()

app = Flask(__name__)
# Configure image upload destination
app.config['UPLOADED_IMAGES_DEST'] = 'static/item_images'
app.config['UPLOADED_IMAGES_URL'] = 'item_images/'

configure_uploads(app, uploaded_images)


def Response(response={}, error=None, response_code=200):
    """Helper function to generate a request response."""
    if response_code == 200 and error:
        response_code = 500

    return (jsonify(
        error if error
        else response),
        response_code)


def generate_state():
    """Generates a random token for session state."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(32))


def requires_authentication(f):
    """Decorator that checks if the user is currently logged in."""

    def decorator(*args, **kwargs):
        if 'userid' not in login_session:
            return Response(
                error='Request requires authentication', response_code=401)

        return f(*args, **kwargs)

    return update_wrapper(decorator, f)


def requires_state_consistency(f):
    """Decorator taht checks if request state parameters is correct."""
    def decorator(*args, **kwargs):
        if ('state' not in request.headers)
        or (request.headers['state'] != login_session['state']):
            return Response(error='Invalid state parameter', response_code=401)

        return f(*args, **kwargs)

    return update_wrapper(decorator, f)


def check_authorization(userid):
    if 'userid' in login_session:
        return login_session['userid'] == userid

    return False


def get_user(email):
    """Searches and returns the user that corresponds to the given email."""
    try:
        return session.query(User).filter(
            User.email == email).one()
    except NoResultFound:
        return None
    except:
        return None


def add_user(email, name):
    """Creates user entry."""
    try:
        new_user = User(email=email, name=name)

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


def get_categories(id=None):
    """If id is set, then it returns the category that matches the id,
    else it returns all category entries."""
    if id is not None:
        try:
            response = Response(session.query(Category).filter(
                Category.id == id).one().tojson())
        except NoResultFound:
            response = Response([])
        except:
            response = Response(
                error='Unknown error',
                response_code=500)

        return response
    else:
        category_list = []

        for category in session.query(Category).all():
            category_list.append(category.tojson())

        return Response(category_list) if len(category_list) > 0 \
            else Response([])


@requires_authentication
@requires_state_consistency
def add_category(name):
    """Creates category entry."""
    owner_id = login_session['userid']

    try:
        newCategory = Category(name=name, owner_id=owner_id)

        session.add(newCategory)
        session.commit()

        return Response(newCategory.tojson())
    except IntegrityError:
        session.rollback()
        return Response(
            error='Invalid new category parameters. '
            '(name: {}, owner_id: {})'.format(name, owner_id),
            response_code=400)
    except InvalidRequestError as e:
        print(e)
        return Response(
            error='Failed to add new category',
            response_code=400)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to add new category',
            response_code=500)


@requires_authentication
@requires_state_consistency
def delete_category(id):
    """Deletes category that matches given id."""
    try:
        category = session.query(Category).filter(Category.id == id).one()

        if not check_authorization(category.owner_id):
            return Result(
                error='Permission denied',
                response_code=401)

        session.delete(category)
        session.commit()
        return Response('Success')

    except DataError:
        return Response(
            error='Category id is not an integer',
            response_code=400)
    except NoResultFound:
        return Response(
            error='There is no category that corresponds '
            'to the specified id. (id: {})'.format(id),
            response_code=400)
    except InternalError as e:
        print(e)
        return Response(
            error='Failed to delete category with id: {}'.format(id),
            response_code=500)
    except IntegrityError as e:
        print(e)
        session.rollback()
        return Response(
            error='Failed to delete category with id: {}'.format(id),
            response_code=400)
    except InvalidRequestError as e:
        print(e)
        return Response(
            error='Failed to delete category with id: {}'.format(id),
            response_code=400)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to delete category with id: {}'.format(id),
            response_code=500)


def get_items(id=None):
    """If id is set, then it returns the item that matches the id,
    else it returns all item entries."""
    if id is not None:
        try:
            response = Response(session.query(Item).filter(
                Item.id == id).one().tojson())
        except NoResultFound:
            response = Response([])
        except:
            response = Response(
                error='Unknown error',
                response_code=500)

        return response
    else:
        item_list = []

        for item in session.query(Item).all():
            item_list.append(item.tojson())

        return Response(item_list) if len(item_list) > 0\
            else Response([])


@requires_authentication
@requires_state_consistency
def add_item(name, category_id, description=None, image_id=None):
    """Creates item entry."""
    owner_id = login_session['userid']

    # This ensures that the category set is also owned by the user
    try:
        category = session.query(Category)\
            .filter(Category.id == category_id).one()
    except NoResultFound:
        return Response(
            error='Invalid category id',
            response_code=400)
    except:
        return Response(
            error='Unknown error',
            response_code=500)

    if not check_authorization(category.owner_id):
        return Result(
            error='Permission denied for given category id.',
            response_code=401)

    # This ensures that the image set (if set) is also owned by the user
    if image_id:
        try:
            image = session.query(Image)\
                .filter(Image.id == image_id).one()
        except NoResultFound:
            return Response(
                error='Invalid image id',
                response_code=400)
        except:
            return Response(
                error='Unknown error',
                response_code=500)

        if not check_authorization(image.owner_id):
            return Result(
                error='Permission denied for given image id.',
                response_code=401)

    try:
        newItem = Item(
            name=name,
            description=description,
            owner_id=owner_id,
            category_id=category_id,
            image_id=image_id)

        session.add(newItem)
        session.commit()

        return Response(newItem.tojson())
    except IntegrityError as e:
        print(e)
        session.rollback()
        return Response(
            error='Invalid new item parameters. '
            '(name: {}, '
            'description: {}, '
            'category_id: {}, '
            'owner_id: {}, '
            'image_id: {})'
            .format(name,
                    description,
                    category_id,
                    owner_id,
                    image_id),
            response_code=400)
    except InvalidRequestError as e:
        print(e)
        return Response(
            error='Failed to add new item',
            response_code=400)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to add new item',
            response_code=500)


@requires_authentication
@requires_state_consistency
def update_item(
        id,
        name=None,
        category_id=None,
        description=None,
        image_id=None):
    """Updates item entry."""
    try:
        target = session.query(Item).filter(Item.id == id).one()
    except NoResultFound:
        return Response(error='No result found',
                        response_code=400)
    except:
        return Response(
            error='Unknown error',
            response_code=500)
    else:
        if not check_authorization(target.owner_id):
            return Result(
                error='Permission denied',
                response_code=401)

        updated = False

        if name and (target.name != name):
            target.name = name
            updated = True

        if category_id and (target.category_id != category_id):
            # This ensures that the category set is also owned by the user
            try:
                category = session.query(Category)\
                    .filter(Category.id == category_id).one()
            except NoResultFound:
                return Response(
                    error='Invalid category id',
                    response_code=400)
            except:
                return Response(
                    error='Unknown error',
                    response_code=500)

            if not check_authorization(category.owner_id):
                return Result(
                    error='Permission denied for given category id.',
                    response_code=401)

            target.category_id = category_id
            updated = True

        if description and (target.description != description):
            target.description = description
            updated = True

        if image_id and (target.image_id != image_id):
            # This ensures that the image set
            # (if set) is also owned by the user
            try:
                image = session.query(Image)\
                    .filter(Image.id == image_id).one()
            except NoResultFound:
                return Response(
                    error='Invalid image id',
                    response_code=400)
            except:
                return Response(
                    error='Unknown error',
                    response_code=500)

            if not check_authorization(image.owner_id):
                return Result(
                    error='Permission denied for given image id.',
                    response_code=401)
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
                return Response(
                    error='Invalid new item parameters. '
                    '(name: {}, '
                    'description: {}, '
                    'category_id: {}, '
                    'image_id: {})'
                    .format(name, description, category_id, image_id),
                    response_code=400)
            except InvalidRequestError as e:
                print(e)
                return Response(
                    error='Failed to update item',
                    response_code=400)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                return Response(
                    error='Failed to update item',
                    response_code=500)
        else:
            return Response('Item has not changed')


@requires_authentication
@requires_state_consistency
def delete_item(id):
    """Deletes item that matches given id."""
    try:
        target = session.query(Item).filter(Item.id == id).one()

        if not check_authorization(target.owner_id):
            return Result(
                error='Permission denied',
                response_code=401)

        image = target.image

        session.delete(target)
        session.commit()

        return Response('Success')
    except DataError:
        return Response(
            error='Item id is not an integer',
            response_code=400)
    except NoResultFound:
        return Response(
            error='There is no item that corresponds '
            'to the specified id. (id: {})'.format(id),
            response_code=400)
    except InternalError as e:
        print(e)
        return Response(
            error='Failed to delete item with id: {}'.format(id),
            response_code=500)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to delete item with id: {}'.format(id),
            response_code=500)


@requires_authentication
@requires_state_consistency
def add_image(path):
    """Create image entry."""
    owner_id = login_session['userid']

    try:
        newimage = Image(path=path, owner_id=owner_id)

        session.add(newimage)
        session.commit()

        return Response(newimage.tojson())
    except IntegrityError as e:
        print(e)
        session.rollback()
        return Response(
            error='Invalid new image parameter. (path: {})'
            .format(path),
            response_code=400)
    except InvalidRequestError as e:
        print(e)
        return Response(
            error='Failed to add new image',
            response_code=400)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to add new image',
            response_code=500)


@requires_authentication
@requires_state_consistency
def update_image(id, path=None):
    """Updates image path entry.

    It also deletes image associated with old path."""
    if not path:
        return Response(error='Missing path parameter',
                        response_code=400)

    try:
        target = session.query(Image).filter(Image.id == id).one()
    except NoResultFound:
        return Response(error='No result found',
                        response_code=400)
    except:
        return Response(
            error='Unknown error',
            response_code=500)
    else:
        if not check_authorization(target.owner_id):
            return Result(
                error='Permission denied',
                response_code=401)

        if path == target.path:
            return Response('Item has not changed')

        file_path = uploaded_images.path(target.path)
        os.remove(file_path)

        target.path = path

        try:
            session.add(target)
            session.commit()

            return Response('Success')
        except IntegrityError as e:
            print(e)
            session.rollback()
            return Response(
                error='Invalid new image parameters. (path: {})'
                .format(path),
                response_code=400)
        except InvalidRequestError as e:
            print(e)
            return Response(
                error='Failed to update image',
                response_code=400)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return Response(
                error='Failed to update image',
                response_code=500)


@requires_authentication
@requires_state_consistency
def delete_image(id):
    """Deletes image and image file that matches given id."""
    try:
        target = session.query(Image).filter(Image.id == id).one()

        if not check_authorization(target.owner_id):
            return Result(
                error='Permission denied',
                response_code=401)

        file_path = uploaded_images.path(target.path)
        os.remove(file_path)

        session.delete(target)
        session.commit()

        return Response('Success')
    except DataError:
        return Response(
            error='Image id is not an integer',
            response_code=400)
    except NoResultFound:
        return Response(
            error='There is no image that corresponds '
                  'to the specified id. (id: {})'.format(id),
            response_code=400)
    except InternalError as e:
        print(e)
        return Response(
            error='Failed to delete image with id: {}'.format(id),
            response_code=500)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return Response(
            error='Failed to delete image with id: {}'.format(id),
            response_code=500)


class RateLimit(object):
    """Class used to control access frequency for a given endpoint."""
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
    return (jsonify({'data': 'You hit the rate limit', 'error': '429'}), 429)


def ratelimit(limit, per=300, send_x_headers=True,
              over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    """Decorator used to control access frequency for given function."""
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
    """Add limits feedback on response headers."""
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
    """Route for the Item Catalog App page."""
    state = generate_state()
    login_session['state'] = state

    return render_template('index.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
@requires_state_consistency
@ratelimit(limit=30, per=60 * 1)
def gconnect():
    """Endpoint that authenticates user."""
    try:
        idinfo = client.verify_id_token(
            request.data,
            '1014623565180-lm2sl4gftjv5r8jhgikg0ti9lcldol8c'
            '.apps.googleusercontent.com')

        if idinfo['iss'] not in ['accounts.google.com',
                                 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError:
        return (jsonify(
            {'data': 'Invalid authentication issuer',
             'error': '401'}), 401)

    user = get_user(idinfo['email'])

    if user is None:
        user = add_user(idinfo['email'], idinfo['name'])

        if user is None:
            return (jsonify({'data': 'Internal Error', 'error': '500'}), 500)

    login_session['userid'] = user.id

    return Response(
        {'user_id': user.id,
         'user_name': idinfo['name'],
         'user_picture': idinfo['picture']})


@app.route('/gdisconnect', methods=['POST'])
@ratelimit(limit=30, per=60 * 1)
@requires_authentication
@requires_state_consistency
def gdisconnect():
    """Endpoint that signs user off the application."""
    del login_session['userid']

    return Response('User disconnected successfully')


@app.route('/api/category',
           defaults={'category': None},
           methods=['GET', 'POST', 'DELETE'])
@app.route('/api/category/<int:category>',
           methods=['GET', 'DELETE'])
@ratelimit(limit=10, per=60 * 1)
def api_category(category):
    """Endpoint for the category CRUD operations."""
    if request.method == 'GET':
        return get_categories(category)

    elif request.method == 'POST':
        if 'name' in request.json:
            return add_category(name=request.json['name'])
        else:
            return Response(
                error='Missing "name" parameter',
                response_code=400)

    elif request.method == 'DELETE':
        if category:
            return delete_category(category)
        elif 'id' in request.json:
            return delete_category(request.json['id'])
        else:
            return Response(
                error='Missing "id" parameter',
                response_code=400)
    else:
        return Response(
            error='Method is not yet implemented',
            response_code=400)


@app.route('/api/item',
           defaults={'item': None},
           methods=['GET', 'POST', 'DELETE'])
@app.route('/api/item/<int:item>',
           methods=['GET', 'DELETE', 'PATCH'])
@ratelimit(limit=10, per=60 * 1)
def api_item(item):
    """Endpoint for the item CRUD operations."""
    if request.method == 'GET':
        return get_items(item)

    elif request.method == 'POST':
        if ('name' in request.json) and ('category_id' in request.json):
            return add_item(**request.json)
        else:
            return Response(
                error='Missing "name" '
                      'or "category_id" parameters',
                response_code=400)

    elif request.method == 'DELETE':
        if item:
            return delete_item(item)
        elif 'id' in request.json:
            return delete_item(request.json['id'])
        else:
            return Response(
                error='Missing "id" parameter',
                response_code=400)

    elif request.method == 'PATCH':
        return update_item(item, **request.json)
    else:
        return Response(
            error='Method is not yet implemented',
            response_code=405)


@app.route('/api/image',
           defaults={'image': None},
           methods=['GET', 'POST', 'DELETE'])
@app.route('/api/image/<int:image>',
           methods=['GET', 'DELETE', 'PATCH'])
@ratelimit(limit=10, per=60 * 1)
def api_image(image):
    """Endpoint for the image CRUD operations."""
    if request.method == 'GET':
        return get_images(image)

    elif request.method == 'POST':
        image_file = request.files.get('image')

        if image_file:
            try:
                filename = uploaded_images.save(image_file)
            except UploadNotAllowed:
                return Response(
                    error='Image upload not allowed',
                    response_code=400)
            else:
                return add_image(filename)
        else:
            return Response(
                error='Missing image file ',
                response_code=400)

    elif request.method == 'DELETE':
        if image:
            return delete_image(image)
        elif 'id' in request.json:
            return delete_image(request.json['id'])
        else:
            return Response(
                error='Missing "id" parameter',
                response_code=400)

    elif request.method == 'PATCH':
        image_file = request.files.get('image')

        if image_file:
            try:
                filename = uploaded_images.save(image_file)
            except UploadNotAllowed:
                return Response(
                    error='Image upload not allowed',
                    response_code=400)
            else:
                return update_image(image, filename)
        else:
            return Response(
                error='Missing image file ',
                response_code=400)
    else:
        return Response(
            error='Method is not yet implemented',
            response_code=405)

if __name__ == '__main__':
    app.secret_key = 'i3Ldm4dv8c9sBsc45A3vx6sO3plsn'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
