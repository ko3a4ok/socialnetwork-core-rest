import json
import time
from core.posts import ERROR_POST_NOT_FOUND, CREATED_AT, CREATED_BY
from core.users import get_user

__author__ = 'ko3a4ok'
import bson
from flask import request
import flask
from flask.ext.login import login_required, current_user

from core import app
from core import mongo

COMMENTS = "comments"


@app.route('/post/<post_id>/comment', methods=['POST'])
@login_required
def comment(post_id):
    post_id = bson.ObjectId(post_id)
    my_id = bson.ObjectId(current_user.id)
    r = mongo.db.posts.find_one({'_id': post_id}, {'_id': 1})
    if not r:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    new_params = json.loads(request.data.decode('utf8'))
    new_params[CREATED_AT] = time.time()
    new_params[CREATED_BY] = my_id
    new_params['_id'] = bson.ObjectId()
    mongo.db.posts.update({'_id': post_id}, {'$addToSet': {COMMENTS: new_params}})
    p = {'$project': {COMMENTS + '_count': {'$size': {'$ifNull': ["$" + COMMENTS, []]}}}}
    ar = mongo.db.posts.aggregate([{'$match': {'_id': post_id}}, p])
    comments_count = ar['result'][0]
    new_params[CREATED_BY] = get_user(str(new_params[CREATED_BY]))
    comments_count['last_comment'] = new_params
    mongo.db.posts.update({'_id': post_id}, {'$set': comments_count})
    return bson.json_util.dumps(comments_count)


@app.route('/post/<post_id>/comment/<comment_id>', methods=['PUT', 'DELETE'])
@login_required
def update_comment(post_id, comment_id):
    post_id = bson.ObjectId(post_id)
    comment_id = bson.ObjectId(comment_id)
    r = mongo.db.posts.find_one({'_id': post_id}, {'_id': 1, CREATED_BY: 1})
    if not r:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    my_id = bson.ObjectId(current_user.id)
    post_author = bson.ObjectId(r[CREATED_BY])
    global r
    if request.method == 'PUT':
        new_params = json.loads(request.data.decode('utf8'))
        store_values = {(COMMENTS + '.$.' + key): value for key, value in new_params.items()}
        r = mongo.db.posts.update(
            {"_id": post_id, COMMENTS + "._id": comment_id, CREATED_BY: my_id},
            {'$set': store_values}
        )
    else:
        selection = {"_id": post_id, COMMENTS + "._id": comment_id}
        if post_author != my_id:
            selection[CREATED_BY] = my_id
        r = mongo.db.posts.update(
            selection,
            {'$pull': {COMMENTS: {'_id':  comment_id}}}
        )
    result = r['updatedExisting']
    if result:
        r = mongo.db.posts.find_one({'_id': post_id}, {COMMENTS: {'$slice': -1}})
        new_params = None
        if len(r[COMMENTS]) > 0:
            new_params = r[COMMENTS][0]
            new_params[CREATED_BY] = get_user(str(new_params[CREATED_BY]))
        mongo.db.posts.update({'_id': post_id}, {'$set': {'last_comment': new_params}})
        if request.method == 'DELETE':
            p = {'$project': {COMMENTS + '_count': {'$size': {'$ifNull': ["$" + COMMENTS, []]}}}}
            ar = mongo.db.posts.aggregate([{'$match': {'_id': post_id}}, p])
            comments_count = ar['result'][0]
            mongo.db.posts.update({'_id': post_id}, {'$set': comments_count})
    return json.dumps({'result': result})


@app.route('/post/<post_id>/comment')
@login_required
def get_comments(post_id):
    post_id = bson.ObjectId(post_id)
    r = mongo.db.posts.find_one({'_id': post_id}, {'_id': 1})
    if not r:
        return flask.make_response(ERROR_POST_NOT_FOUND, 404)
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    comments = mongo.db.posts.find_one({'_id': post_id}, {COMMENTS: {'$slice': [offset, limit]}})[COMMENTS]
    for comment in comments:
            comment[CREATED_BY] = get_user(str(comment[CREATED_BY]))
    return bson.json_util.dumps({COMMENTS: comments})

