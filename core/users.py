from functools import wraps
import json
from multiprocessing.pool import ThreadPool
import bson
from flask import request
import flask
from flask.ext.login import login_user, current_user, UserMixin, login_required
import bson.objectid
import requests
import core.utils
from core import app, login_manager, redis, search, SEARCH_INDEX
from core import mongo
from flask.ext.cors import cross_origin


ACCESS_TOKEN = "access_token"
FACEBOOK_ID = "facebook_id"
EMAIL = 'email'
PASSWORD = 'password'
NAME = 'name'
FOLLOWERS = 'followers'
FOLLOWING = 'following'
PROPERTIES = {PASSWORD: 0, FOLLOWING: 0, FOLLOWERS: 0}
ERROR_FACEBOOK_ACCESS_TOKEN = 'Please provide access token'
ERROR_USER_EXISTS = 'Sorry, user with this email has already registered'
ERROR_WRONG_CREDENTIALS = 'Sorry, wrong credentials'
ERROR_USER_NOT_FOUND = 'Sorry, user not found'
FAST_USER_PROPERTIES = ['_id', 'name', 'mini_profile_url']
pool = ThreadPool(processes=5)


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)

    return decorated_function


class User(UserMixin):
    def __init__(self, u):
        self.id = str(u['_id'])


@app.route('/user/register', methods=['POST'])
def register():
    mail = request.form[EMAIL]
    a = mongo.db.users.find({EMAIL: mail}).limit(1)
    if a.count() > 0:
        return flask.make_response(ERROR_USER_EXISTS, 409)
    user = {EMAIL: mail, PASSWORD: request.form[PASSWORD]}
    mongo.db.users.insert(user)
    del user[PASSWORD]
    login_user(User(user))
    return bson.json_util.dumps(user)


@app.route("/user/facebook", methods=['POST'])
def facebook():
    host = "https://graph.facebook.com/v2.5"
    path = "/me?fields=id,name,birthday,gender"
    access_token = request.form[ACCESS_TOKEN]
    if not access_token: return flask.make_response(ERROR_FACEBOOK_ACCESS_TOKEN, 401)
    url = '{host}{path}&access_token={access_token}'.format(host=host, path=path, access_token=access_token)
    response = requests.get(url)
    if response.status_code != 200:
        return flask.make_response(response.content, 401)
    user = json.loads(response.content)

    cur = mongo.db.users.find({FACEBOOK_ID: user['id']}, {PASSWORD: 0})
    if not cur.count():
        if 'gender' in user:
            user['sex'] = user.pop('gender')
        if 'birthday' in user:
            bparts = user['birthday'].split('/')
            user['birthday'] = '/'.join(bparts[1::-1] + bparts[2:])
        photo_url = host + "/me/picture?type=large&access_token=" + access_token + "&redirect=false"
        mini_photo_url = host + "/me/picture?type=square&access_token=" + access_token + "&redirect=false"
        user[FACEBOOK_ID] = user.pop('id')
        user['profile_url'] = requests.get(photo_url).json()['data']['url']
        user['mini_profile_url'] = requests.get(mini_photo_url).json()['data']['url']
        user[PASSWORD] = None
        mongo.db.users.insert(user)
    user = cur[0]
    login_user(User(user))
    return bson.json_util.dumps(user)

@app.route('/user/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def login():
    user = {EMAIL: request.form[EMAIL], PASSWORD: request.form[PASSWORD]}
    cur = mongo.db.users.find(user, {PASSWORD: 0})
    if cur.count() == 0:
        return flask.make_response(ERROR_WRONG_CREDENTIALS, 401)
    user = cur[0]
    login_user(User(user))
    return bson.json_util.dumps(user)


def _update_user_in_search_db(user):
    id = str(user['_id'])
    del user[EMAIL]
    del user['_id']
    user['user_id'] = id
    search.index(SEARCH_INDEX, doc_type="user", id=id, body=bson.json_util.dumps(user))


@app.route('/user/me', methods=['GET', 'POST'])
@login_required
@support_jsonp
def settings():
    id = bson.ObjectId(current_user.id)
    if request.method == 'POST':
        new_params = json.loads(request.data.decode('utf8'))
        mongo.db.users.update({'_id': id}, {'$set': new_params})
        redis.hmset(current_user.id, new_params)
        user = mongo.db.users.find_one({'_id': bson.ObjectId(id)}, PROPERTIES)
        pool.apply_async(_update_user_in_search_db, kwds={'user': user})
    return user_profile(id)


@app.route('/user/<id>')
@login_required
def user_profile(id):
    try:
        id = bson.ObjectId(id)
        q = {'_id': id}
        p = {'$project': {FOLLOWING + '_count': {'$size': {'$ifNull': ["$" + FOLLOWING, []]}},
                          FOLLOWERS + '_count': {'$size': {'$ifNull': ["$" + FOLLOWERS, []]}}}}
        res = mongo.db.users.find_one(q, PROPERTIES)
        if not res:
            raise AttributeError
        ar = mongo.db.users.aggregate([{'$match': q}, p])
        res.update(ar['result'][0])
        mydata = bson.json_util.dumps(res)
        return flask.Response(mydata, mimetype='application/json')
    except:
        return flask.make_response(ERROR_USER_NOT_FOUND, 404)


@login_manager.user_loader
def load_user(user_id):
    return User(get_user(user_id))


def get_user(user_id):
    user = get_user_fast(user_id)
    if not user:
        id = bson.ObjectId(user_id)
        cur = mongo.db.users.find({'_id': id}, PROPERTIES)
        if cur.count() == 0:
            return None
        user = cur[0]
        redis.hmset(user_id, user)
    return user


def get_user_fast(user_id):
    r = redis.hmget(user_id, FAST_USER_PROPERTIES)
    if r.count(None) == len(r):
        return None
    return dict(zip(FAST_USER_PROPERTIES, r))


def user_list_output(user_ids, offset, limit):
    users = map(get_user, user_ids)
    return bson.json_util.dumps({'offset': offset, 'limit': limit, 'users': users})


@app.route('/user/find')
def search_user():
    q = {
        'from': int(request.args.get('offset', 0)),
        'size': int(request.args.get('limit', 10)),
        'query': {
            'match': {
                'name': request.args.get('q', '')
            }
        }
    }

    res = search.search(index=SEARCH_INDEX, doc_type='user', body=q)
    total = res['hits']['total']
    users = []
    for hit in res['hits']['hits']:
        user = hit['_source']
        user['_id'] = user.pop('user_id')
        users.append(user)
    result = {
        'total': total,
        'users': users
    }
    return bson.json_util.dumps(result)
