import json
import bson
from flask import request
import flask
from flask.ext.login import login_required, current_user
import time
import core
from core.follow import FOLLOWING

__author__ = 'ko3a4ok'

from core import app
from core import mongo
from core.users import get_user, ERROR_USER_NOT_FOUND

CREATED_AT = 'created_at'
CREATED_BY = 'created_by'
UPDATED_AT = 'updated_at'

POSTS = 'posts'

ERROR_POST_NOT_FOUND = 'Sorry, but post not found'

@app.route('/post', methods=['POST'])
@login_required
def post():
    new_params = json.loads(request.data.decode('utf8'))
    new_params[CREATED_AT] = time.time()
    new_params[CREATED_BY] = bson.ObjectId(current_user.id)
    result = mongo.db[POSTS].insert(new_params)
    return bson.json_util.dumps({'_id': result})


@app.route('/user/<user_id>/post/<post_id>')
@login_required
def get_post(user_id, post_id):
    post_id = bson.ObjectId(post_id)
    r = mongo.db[POSTS].find_one({'_id': post_id})
    if not r:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    r[CREATED_BY] = core.users.get_user_fast(user_id)
    return bson.json_util.dumps(r)


@app.route('/user/me/post/<post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    post_id = bson.ObjectId(post_id)
    new_params = json.loads(request.data.decode('utf8'))
    new_params[UPDATED_AT] = time.time()
    r = mongo.db[POSTS].update({'_id': post_id, CREATED_BY: bson.ObjectId(current_user.id)}, {'$set': new_params})
    if not r['updatedExisting']:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    return bson.json_util.dumps({'_id': post_id})


@app.route('/user/me/post/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post_id = bson.ObjectId(post_id)
    r = mongo.db[POSTS].remove({'_id': post_id, CREATED_BY: bson.ObjectId(current_user.id)}, True)
    if not r['n']:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    return '{}'


@app.route('/timeline/<user_id>')
@login_required
def timeline(user_id):
    user = get_user(user_id)
    if not user:
        return flask.make_response(ERROR_USER_NOT_FOUND, 404)
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    uid = bson.ObjectId(current_user.id)
    r = mongo.db[POSTS].find({CREATED_BY: uid}).sort([(CREATED_AT, -1)]).skip(offset).limit(limit)
    posts = list(r)
    for post in posts:
        post[CREATED_BY] = user
    return bson.json_util.dumps({'posts': posts})


@app.route('/feed')
@login_required
def feed():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    uid = bson.ObjectId(current_user.id)
    f = mongo.db.users.find_one({'_id': uid}, {'_id': 0, FOLLOWING: 1})
    following = f[FOLLOWING] + [uid]
    r = mongo.db[POSTS].find({CREATED_BY: {"$in": following}}).sort([(CREATED_AT, -1)]).skip(offset).limit(limit)
    posts = list(r)
    for post in posts:
        post[CREATED_BY] = get_user(str(post[CREATED_BY]))
    return bson.json_util.dumps({'posts': posts})
