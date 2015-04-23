import json
from bson import json_util
import bson
from flask import request, abort
import flask
from core import app
from core import mongo

EMAIL = 'email'
PASSWORD = 'password'
NAME = 'name'


__author__ = 'ko3a4ok'
ERROR_USER_EXISTS = 'Sorry, user with this email has already registered'
ERROR_WRONG_CREDENTIALS = 'Sorry, wrong credentials'


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
    return bson.json_util.dumps(cur[0], default=json_util.default)
