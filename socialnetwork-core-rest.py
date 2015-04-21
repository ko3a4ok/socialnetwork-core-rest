import json
import os
import bson
from flask import Flask, request
from flask.ext.pymongo import PyMongo
import yaml
from bson import BSON
from bson import json_util

app = Flask(__name__)
MONGO_CONFIG = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/mongo_config.yaml'))
app.config.update(MONGO_CONFIG)
mongo = PyMongo(app)


@app.route('/users/', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        user = {k: v for k, v in request.form.items()}
        mongo.db.users.insert(user)
        return ''
    return bson.json_util.dumps(mongo.db['users'].find(), default=json_util.default)

@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)
