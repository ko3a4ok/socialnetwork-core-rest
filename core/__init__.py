import os

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.pymongo import PyMongo
import yaml

app = Flask(__name__)
login_manager = LoginManager(app)
MONGO_CONFIG = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../mongo_config.yaml'))
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

import core.users

@app.route('/')
def hello_world():
    return 'Hello World!'


