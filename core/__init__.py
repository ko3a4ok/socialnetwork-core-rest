import os

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.pymongo import PyMongo
from redis import Redis

app = Flask(__name__)
login_manager = LoginManager(app)
print('MONGOURL: ', os.environ.get('MONGOLAB_URI'))
MONGO_CONFIG = {'MONGO_URI': os.environ.get('MONGOLAB_URI')}
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
redis = Redis.from_url(os.environ.get('REDISCLOUD_URL'))

import core.users
import core.follow
import core.posts

@app.route('/')
def hello_world():
    return 'REST API for social network template'


