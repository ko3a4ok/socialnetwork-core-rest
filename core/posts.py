import json
import bson
from flask import request
import flask
from flask.ext.login import login_required, current_user
import time
import core

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
    result = mongo.db[POSTS + "_" + current_user.id].insert(new_params)
    return bson.json_util.dumps({'_id': result})


@app.route('/user/<user_id>/post/<post_id>')
@login_required
def get_post(user_id, post_id):
    post_id = bson.ObjectId(post_id)
    r = mongo.db[POSTS + "_" + user_id].find_one({'_id': post_id})
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
    r = mongo.db[POSTS + "_" + current_user.id].update({'_id': post_id}, {'$set': new_params})
    if not r['updatedExisting']:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    return bson.json_util.dumps({'_id': post_id})


@app.route('/user/me/post/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post_id = bson.ObjectId(post_id)
    r = mongo.db[POSTS + "_" + current_user.id].remove({'_id': post_id}, True)
    if not r['n']:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    return '{}'


@app.route('/timeline/<user_id>')
@login_required
def timeline(user_id):
    user = get_user(user_id)
    if not user:
        return flask.make_response(ERROR_USER_NOT_FOUND, 404)
    t = POSTS + "_" + user_id
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    cnt = mongo.db[t].count()
    skip = cnt-offset-limit
    if skip < 0:
        limit += skip
        skip = 0
    r = mongo.db[t].find().skip(skip).limit(limit)
    posts = reversed(list(r))
    for post in posts:
        post[CREATED_BY] = user
    return bson.json_util.dumps({'posts': posts})
