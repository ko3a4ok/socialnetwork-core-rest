import json
from unittest import TestCase
import unittest
import uuid

import core


__author__ = 'ko3a4ok'


class UserRegistration(TestCase):
    def __init__(self, *a, **m):
        super(UserRegistration, self).__init__(*a, **m)
        self.email = uuid.uuid4()
        self.password = uuid.uuid4()

    def setUp(self):
        core.app.config['TESTING'] = True
        self.app = core.app.test_client()

    def tearDown(self):
        pass

    def test_create_new_user(self):
        data = dict(
            email=self.email,
            password=self.password)
        res = self.app.post('/user/register', data=data)
        assert res.status_code == 200

    def test_login_user(self):
        self.test_create_new_user()
        data = dict(
            email=self.email,
            password=self.password)
        res = self.app.post('/user/login', data=data)
        assert res.status_code == 200
        self.cookie = self.app.cookie_jar._cookies['localhost.local']['/']['session'].value

    def test_user_me(self):
        self.test_login_user()
        self.app.set_cookie('localhost.local', 'session')
        res = self.app.get('/user/me')
        assert res.status_code == 401
        self.app.set_cookie('localhost.local', 'session', value=self.cookie)
        res = self.app.get('/user/me')
        assert res.status_code == 200
        name = str(uuid.uuid4())
        res = self.app.post('/user/me', data=json.dumps({'name': name}))
        assert res.status_code == 200
        res = self.app.get('/user/me')
        assert res.status_code == 200
        assert json.loads((res.data.decode('utf8')))['name'] == name

    def test_get_user(self):
        self.test_login_user()
        res = self.app.get('/user/' + str(uuid.uuid4()))
        assert res.status_code == 404
        res = self.app.get('/user/me')
        orig = json.loads((res.data.decode('utf8')))
        user_id = orig['_id']
        res = self.app.get('/user/' + user_id)
        assert orig == json.loads((res.data.decode('utf8')))

if __name__ == '__main__':
    unittest.main()