from collections import deque
from itertools import izip
import json
import time
import itertools
from core.posts import UPDATED_AT, CREATED_BY

__author__ = 'ko3a4ok'
from test_follow import app, DEFAULT_PASSWORD
from test_follow import auth_app
from test_follow import generated_users


def test_create_post(auth_app):
    orig_post = {"text": "Test message"}
    r = auth_app.post('/post', data=json.dumps(orig_post))
    assert r.status_code == 200
    global post_id
    post_id = json.loads(r.data.decode('utf8'))['_id']
    res = auth_app.get('/user/me')
    global my_id
    my_id = json.loads((res.data.decode('utf8')))['_id']
    r = auth_app.get('/post/{}'.format(post_id))
    assert r.status_code == 200
    post = json.loads(r.data.decode('utf8'))
    assert post['text'] == orig_post['text']
    assert my_id == post['created_by']['_id']
    

def test_update_post(auth_app):
    global post_id, my_id
    new_post = {"text": "Changed post"}
    r = auth_app.put('/user/me/post/{}'.format(post_id), data=json.dumps(new_post))
    assert r.status_code == 200
    r = auth_app.get('/post/{}'.format(post_id))
    assert r.status_code == 200
    post = json.loads(r.data.decode('utf8'))
    assert post[UPDATED_AT]
    assert post['text'] == new_post['text']


def test_delete_post(auth_app):
    global post_id, my_id
    r = auth_app.delete('/user/me/post/{}'.format(post_id))
    assert r.status_code == 200
    r = auth_app.get('/post/{}'.format(post_id))
    assert r.status_code == 404


def test_post_not_found(auth_app):
    not_exist_post_id = '0'*24
    r = auth_app.get('/post/{}'.format(not_exist_post_id))
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
    before = 'f'*24
    for idx, post in enumerate(orig_posts):
        r = auth_app.post('/post', data=json.dumps(post))
        assert r.status_code == 200
        if idx == post_cnt-offset:
            before = json.loads(r.data.decode('utf8'))['_id']

    r = auth_app.get('/timeline/{}?before={}&limit={}'.format(my_id, before, limit))
    posts = json.loads(r.data.decode('utf8'))['posts']
    subset_orig_posts = orig_posts[post_cnt-offset-limit:post_cnt-offset]
    subset_orig_posts.reverse()

    for orig_post, post in izip(subset_orig_posts, posts):
        assert post[CREATED_BY]['_id'] == my_id
        assert post['text'] == orig_post['text']


def _post_message_by_user(app, user):
    data = dict(
            email=user['email'],
            password=DEFAULT_PASSWORD
    )
    r = app.post('/user/login', data=data)
    orig = json.loads((r.data.decode('utf8')))

    assert r.status_code == 200
    orig_post = {"text": "Message from user {} at ".format(user['email'], str(time.time()))}
    r = app.post('/post', data=json.dumps(orig_post))
    orig_post["_id"] = orig["_id"]
    assert r.status_code == 200
    return orig_post


def test_feed(auth_app, generated_users):
    cookie = auth_app.cookie_jar._cookies['localhost.local']['/']['session'].value
    post_cnt = 30
    offset = 11
    limit = 6
    orig_posts = deque()
    idx = 0
    before = 'f'*24
    for _ in range(post_cnt):
        for user in generated_users:
            orig_posts.appendleft(_post_message_by_user(auth_app, user))
            idx += 1
            if idx == post_cnt*len(generated_users)-offset:
                before = orig_posts[0]['_id']

    subset_orig_posts = list(itertools.islice(orig_posts, offset, offset+limit))
    auth_app.set_cookie('localhost.local', 'session', value=cookie)

    for user in generated_users:
        r = auth_app.post('/user/{}/follow'.format(user['_id']))
        assert r.status_code == 200
    r = auth_app.get('/feed?before={}&limit={}'.format(before, limit))
    posts = json.loads(r.data.decode('utf8'))['posts']

    for orig_post, post in izip(subset_orig_posts, posts):
        assert post[CREATED_BY]['_id'] == orig_post[CREATED_BY]
        assert post['text'] == orig_post['text']

def _like_message_by_user(app, user, post_id, like):
    data = dict(
            email=user['email'],
            password=DEFAULT_PASSWORD
    )
    r = app.post('/user/login', data=data)
    assert r.status_code == 200
    m = app.post if like else app.delete
    r = m('/post/{}/like'.format(post_id))
    assert r.status_code == 200
    return json.loads(r.data.decode('utf8'))


def test_likes(auth_app, generated_users):
    orig_post = {"text": "Test message"}
    r = auth_app.post('/post', data=json.dumps(orig_post))
    assert r.status_code == 200
    post_id = json.loads(r.data.decode('utf8'))['_id']
    likes_count = 0
    for user in generated_users:
        r = _like_message_by_user(auth_app, user, post_id, True)
        likes_count += 1
        assert r['likes_count'] == likes_count

    for user in generated_users:
        r = _like_message_by_user(auth_app, user, post_id, True)
        assert r['likes_count'] == likes_count

    for user in generated_users:
        r = _like_message_by_user(auth_app, user, post_id, False)
        likes_count -= 1
        assert r['likes_count'] == likes_count


def test_likes_not_found(auth_app):
    not_exist_post_id = '0'*24
    r = auth_app.post('/post/{}/like'.format(not_exist_post_id))
    assert r.status_code == 404
    r = auth_app.delete('/user/me/post/{}'.format(not_exist_post_id), data='{}')
    assert r.status_code == 404


def test_own_like(auth_app):
    post_cnt = 20
    orig_posts = [{'text': 'Post message #' + str(_)} for _ in range(post_cnt)]
    liked_posts = set()
    for idx, post in enumerate(orig_posts):
        r = auth_app.post('/post', data=json.dumps(post))
        assert r.status_code == 200
        if idx % 2 == 0:
            orig = json.loads((r.data.decode('utf8')))
            post_id = orig['_id']
            liked_posts.add(post_id)
            r = auth_app.post('/post/{}/like'.format(post_id))
            assert r.status_code == 200
    res = auth_app.get('/user/me')
    my_id = json.loads((res.data.decode('utf8')))['_id']
    r = auth_app.get('/timeline/{}'.format(my_id))
    posts = json.loads(r.data.decode('utf8'))['posts']
    for p in posts:
        assert p['own_like'] == (p['_id'] in liked_posts)


def test_likers(auth_app, generated_users):
    cookie = auth_app.cookie_jar._cookies['localhost.local']['/']['session'].value
    orig_post = {"text": "Test message"}
    r = auth_app.post('/post', data=json.dumps(orig_post))
    assert r.status_code == 200
    post_id = json.loads(r.data.decode('utf8'))['_id']
    for u in generated_users:
        _like_message_by_user(auth_app, u, post_id, True)
    user_ids = {u['_id'] for u in generated_users}
    auth_app.set_cookie('localhost.local', 'session', value=cookie)
    limit = 5
    offset = 0
    while True:
        r = auth_app.get('/post/{}/like?limit={}&offset={}'.format(post_id, limit, offset))
        users = json.loads(r.data.decode('utf8'))['users']
        ids = {u['_id'] for u in users}
        assert ids <= user_ids
        user_ids = user_ids - ids
        offset += limit
        if len(users) < limit:
            break
