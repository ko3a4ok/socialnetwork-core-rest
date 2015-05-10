from itertools import izip
import json
from core.posts import UPDATED_AT, CREATED_BY

__author__ = 'ko3a4ok'
from test_follow import app
from test_follow import auth_app


def test_create_post(auth_app):
    orig_post = {"text": "Test message"}
    r = auth_app.post('/post', data=json.dumps(orig_post))
    assert r.status_code == 200
    global post_id
    post_id = json.loads(r.data.decode('utf8'))['_id']
    res = auth_app.get('/user/me')
    global my_id
    my_id = json.loads((res.data.decode('utf8')))['_id']
    r = auth_app.get('/user/{}/post/{}'.format(my_id, post_id))
    assert r.status_code == 200
    post = json.loads(r.data.decode('utf8'))
    assert post['text'] == orig_post['text']
    assert my_id == post['created_by']['_id']
    

def test_update_post(auth_app):
    global post_id, my_id
    new_post = {"text": "Changed post"}
    r = auth_app.put('/user/me/post/{}'.format(post_id), data=json.dumps(new_post))
    assert r.status_code == 200
    r = auth_app.get('/user/{}/post/{}'.format(my_id, post_id))
    assert r.status_code == 200
    post = json.loads(r.data.decode('utf8'))
    assert post[UPDATED_AT]
    assert post['text'] == new_post['text']


def test_delete_post(auth_app):
    global post_id, my_id
    r = auth_app.delete('/user/me/post/{}'.format(post_id))
    assert r.status_code == 200
    r = auth_app.get('/user/{}/post/{}'.format(my_id, post_id))
    assert r.status_code == 404


def test_post_not_found(auth_app):
    not_exist_post_id = '0'*24
    not_exist_user_id = '0'*24
    r = auth_app.get('/user/{}/post/{}'.format(my_id, not_exist_post_id))
    assert r.status_code == 404
    r = auth_app.get('/user/{}/post/{}'.format(not_exist_user_id, not_exist_post_id))
    assert r.status_code == 404
    r = auth_app.put('/user/me/post/{}'.format(not_exist_post_id), data='{}')
    assert r.status_code == 404
    r = auth_app.delete('/user/me/post/{}'.format(not_exist_post_id))
    assert r.status_code == 404


def test_timeline(auth_app):
    post_cnt = 30
    offset = 11
    limit = 6
    orig_posts = [{'text': 'Post message #' + str(_)} for _ in range(post_cnt)]
    global my_id
    for post in orig_posts:
        r = auth_app.post('/post', data=json.dumps(post))
        assert r.status_code == 200

    r = auth_app.get('/timeline/{}?offset={}&limit={}'.format(my_id, offset, limit))
    posts = json.loads(r.data.decode('utf8'))['posts']
    subset_orig_posts = orig_posts[post_cnt-offset-limit:post_cnt-offset]
    subset_orig_posts.reverse()

    for orig_post, post in izip(subset_orig_posts, posts):
        assert post[CREATED_BY]['_id'] == my_id
        assert post['text'] == orig_post['text']
