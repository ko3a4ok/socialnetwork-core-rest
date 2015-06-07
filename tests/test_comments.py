import json
import random
import pytest

from test_follow import app, auth_app

__author__ = 'ko3a4ok'



@pytest.fixture(scope='module')
def my_id(auth_app):
    res = auth_app.get('/user/me')
    _id = json.loads((res.data.decode('utf8')))['_id']
    return _id


@pytest.fixture(scope='module')
def new_post(auth_app):
    data = {"text": "New post message"}
    res = auth_app.post('/post', data=json.dumps(data))
    res.status_code == 200
    return json.loads(res.data.decode('utf8'))


def test_create_comment(new_post, auth_app):
    post_id = new_post['_id']
    data = {'text': 'Sample comment'}
    res = auth_app.post('/post/{}/comment'.format(post_id), data=json.dumps(data))
    assert res.status_code == 200


def test_last_comment(new_post, auth_app, my_id):
    post_id = new_post['_id']
    data = {'text': 'Sample comment ' + str(random.random())}
    res = auth_app.post('/post/{}/comment'.format(post_id), data=json.dumps(data))
    assert res.status_code == 200
    r = auth_app.get('/timeline/{}'.format(my_id))
    posts = json.loads(r.data.decode('utf8'))['posts']
    assert len(posts) > 0
    last_post = posts[0]
    assert 'last_comment' in last_post and last_post['last_comment'] is not None
    assert data['text'] == last_post['last_comment']['text']
    assert my_id == last_post['last_comment']['created_by']['_id']
    return last_post['last_comment']


def test_update_comment(new_post, auth_app, my_id):
    last_comment = test_last_comment(new_post, auth_app, my_id)
    post_id = new_post['_id']
    data = {'text': 'Updated comment ' + str(random.random())}

    r = auth_app.put('/post/{}/comment/{}'.format(post_id, last_comment['_id']), data=json.dumps(data))
    assert r.status_code == 200
    r = json.loads(r.data.decode('utf8'))
    assert r['result']
    r = auth_app.get('/post/{}/comment?limit={}'.format(post_id, 1000))
    comments = json.loads(r.data.decode('utf8'))['comments']
    for c in comments:
        if c['_id'] == last_comment['_id']:
            assert c['text'] == data['text']
            return
    assert False


def test_delete_comment(new_post, auth_app, my_id):
    last_comment = test_last_comment(new_post, auth_app, my_id)
    post_id = new_post['_id']

    r = auth_app.delete('/post/{}/comment/{}'.format(post_id, last_comment['_id']))
    assert r.status_code == 200
    r = json.loads(r.data.decode('utf8'))
    assert r['result']
    r = auth_app.get('/post/{}/comment?limit={}'.format(post_id, 1000))
    comments = json.loads(r.data.decode('utf8'))['comments']
    for c in comments:
        if c['_id'] == last_comment['_id']:
            assert False
    assert True
