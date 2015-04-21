__author__ = 'ko3a4ok'

import pymongo

client = pymongo.MongoClient(host='192.168.0.104')
print list(client.test.her.find())