import os

from elasticsearch import Elasticsearch
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.login import LoginManager
from flask.ext.pymongo import PyMongo
from redis import Redis

SEARCH_INDEX = "main-index"

app = Flask(__name__)
cors = CORS(app)
login_manager = LoginManager(app)
MONGO_CONFIG = {'MONGO_URI': os.environ.get('MONGOLAB_URI')}
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
redis = Redis.from_url(os.environ.get('REDISCLOUD_URL'))
search = Elasticsearch(os.environ.get('BONSAI_URL'))
search.indices.create(index=SEARCH_INDEX, ignore=400)

import core.users
import core.follow
import core.posts
import core.comments

@app.route('/')
def hello_world():
    r = 'REST API for social network template'
    for rule in app.url_map.iter_rules():
        r += "<br/><a href=\"{link}\">{link}</a>".format(link=str(rule))
    return r
