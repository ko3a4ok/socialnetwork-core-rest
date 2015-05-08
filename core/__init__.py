import os

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.pymongo import PyMongo
from redis import Redis
import yaml

app = Flask(__name__)
login_manager = LoginManager(app)
MONGO_CONFIG = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../config.yaml'))
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
redis = Redis(app.config['REDIS_HOST'], app.config['REDIS_PORT'])

import core.users
import core.follow

@app.route('/')
def hello_world():
    return 'Hello World!'


