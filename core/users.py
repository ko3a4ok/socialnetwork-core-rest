from bson import json_util
import bson
from flask import request
import flask
from flask.ext.login import login_user, current_user, UserMixin, login_required
import bson.objectid

from core import app, login_manager
from core import mongo


EMAIL = 'email'
PASSWORD = 'password'
NAME = 'name'

ERROR_USER_EXISTS = 'Sorry, user with this email has already registered'
ERROR_WRONG_CREDENTIALS = 'Sorry, wrong credentials'


class User(UserMixin):
    def __init__(self, u):
        self.user = u
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
    return bson.json_util.dumps(user, default=json_util.default)


@app.route('/user/login', methods=['POST'])
def login():
    user = {EMAIL: request.form[EMAIL], PASSWORD: request.form[PASSWORD]}
    cur = mongo.db.users.find(user, {PASSWORD: 0})
    if cur.count() == 0:
        return flask.make_response(ERROR_WRONG_CREDENTIALS, 401)
    user = cur[0]
    login_user(User(user))
    return bson.json_util.dumps(user, default=json_util.default)


@app.route('/user/me')
@login_required
def settings():
    return bson.json_util.dumps(current_user.user, default=json_util.default)



@login_manager.user_loader
def load_user(user_id):
    id = bson.ObjectId(user_id)
    cur = mongo.db.users.find({'_id': id}, {PASSWORD: 0})
    user = cur[0]
    return User(user)