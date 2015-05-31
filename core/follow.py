import bson
from flask import request
from flask.ext.login import login_required, current_user

__author__ = 'ko3a4ok'
from core import app
from core import mongo
from core.users import user_list_output, FOLLOWING, FOLLOWERS


@app.route('/user/<id>/follow', methods=['POST'])
@login_required
def follow(id):
    current_user_id = bson.ObjectId(current_user.id)
    user_id = bson.ObjectId(id)
    mongo.db.users.update({'_id': current_user_id}, {'$addToSet': {FOLLOWING: user_id}})
    mongo.db.users.update({'_id': user_id}, {'$addToSet': {FOLLOWERS: current_user_id}})
    return '{}'

@app.route('/user/<id>/follow', methods=['DELETE'])
@login_required
def unfollow(id):
    current_user_id = bson.ObjectId(current_user.id)
    user_id = bson.ObjectId(id)
    mongo.db.users.update({'_id': current_user_id}, {'$pull': {FOLLOWING: user_id}})
    mongo.db.users.update({'_id': user_id}, {'$pull': {FOLLOWERS: current_user_id}})
    return '{}'


def get_connections(id, type_follow):
    current_user_id = bson.ObjectId(current_user.id)
    user_id = bson.ObjectId(id)
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    res = mongo.db.users.find_one({'_id': user_id}, {type_follow: {'$slice': [offset, limit]}})[type_follow]
    return user_list_output(res, offset, limit)

@app.route('/user/<id>/followers')
@login_required
def followers(id):
    return get_connections(id, FOLLOWERS)

@app.route('/user/<id>/following')
@login_required
def following(id):
    return get_connections(id, FOLLOWING)
