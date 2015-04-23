import os

from flask import Flask
from flask.ext.pymongo import PyMongo
import yaml


app = Flask(__name__)
MONGO_CONFIG = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../mongo_config.yaml'))
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)

import users

@app.route('/')
def hello_world():
    return 'Hello World!'


