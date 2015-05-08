import json
import bson
from flask import request
import flask
from flask.ext.login import login_user, current_user, UserMixin, login_required
import bson.objectid
import core.utils
from core import app, login_manager, redis
from core import mongo


EMAIL = 'email'
PASSWORD = 'password'
NAME = 'name'
PROPERTIES = {PASSWORD: 0}
ERROR_USER_EXISTS = 'Sorry, user with this email has already registered'
ERROR_WRONG_CREDENTIALS = 'Sorry, wrong credentials'
ERROR_USER_NOT_FOUND = 'Sorry, user not found'
FAST_USER_PROPERTIES = ['_id', 'name']


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


@app.route('/user/login', methods=['POST'])
def login():
    user = {EMAIL: request.form[EMAIL], PASSWORD: request.form[PASSWORD]}
    cur = mongo.db.users.find(user, {PASSWORD: 0})
    if cur.count() == 0:
        return flask.make_response(ERROR_WRONG_CREDENTIALS, 401)
    user = cur[0]
    login_user(User(user))
    return bson.json_util.dumps(user)


@app.route('/user/me', methods=['GET', 'POST'])
@login_required
def settings():
    id = bson.ObjectId(current_user.id)
    if request.method == 'POST':
        new_params = json.loads(request.data.decode('utf8'))
        mongo.db.users.update({'_id': id}, {'$set': new_params})
    return bson.json_util.dumps(mongo.db.users.find_one({'_id': id}, PROPERTIES))


@app.route('/user/<id>')
@login_required
def get_user(id):
    try:
        id = bson.ObjectId(id)
        res = mongo.db.users.find_one({'_id': id}, PROPERTIES)
        if not res:
            raise AttributeError
        return bson.json_util.dumps(res)
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
