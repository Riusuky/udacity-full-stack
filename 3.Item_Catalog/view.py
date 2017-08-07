from redis import Redis


import time
from functools import update_wrapper
from flask import request, g
from flask import Flask, jsonify

from models import Category, Image, Item

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine('postgresql:///udacity_catalog')

redis = Redis()

db_session = sessionmaker()
db_session.configure(bind=engine)

session = db_session()

app = Flask(__name__)

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

@app.route('/category/')
@ratelimit(limit=30, per=60 * 1)
def page_category():
    return 'Category'

@app.route('/api/category/', defaults={'category': None}, methods=['GET', 'POST', 'DELETE'])
@app.route('/api/category/<int:category>', methods=['GET', 'POST', 'DELETE'])
@ratelimit(limit=10, per=60 * 1)
def api_category(category):
    if category is not None:
        return 'API: Category ({})'.format(category)
    else:
        return 'API: Category'

@app.route('/api/item/', defaults={'item': None}, methods=['GET', 'POST', 'DELETE', 'PATCH'])
@app.route('/api/item/<int:item>', methods=['GET', 'POST', 'DELETE', 'PATCH'])
@ratelimit(limit=10, per=60 * 1)
def api_item(item):
    if item is not None:
        return 'API: Item ({})'.format(item)
    else:
        return 'API: Item'

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
