import json
import uuid
import pytest
import core

__author__ = 'ko3a4ok'

DEFAULT_PASSWORD = uuid.uuid4()


@pytest.fixture(scope='module')
def app():
    core.app.config['TESTING'] = True
    app = core.app.test_client()

    return app


@pytest.fixture(scope='module')
def auth_app(app):
    data = dict(
        email=uuid.uuid4(),
        password=uuid.uuid4())
    res = app.post('/user/register', data=data)
    res.status_code == 200
    cookie = app.cookie_jar._cookies['localhost.local']['/']['session'].value
    app.set_cookie('localhost.local', 'session', value=cookie)
    return app


@pytest.fixture(scope='module')
def generated_users(app):
    cookie = app.cookie_jar._cookies['localhost.local']['/']['session'].value
    users = []
    domain = uuid.uuid4()
    for i in range(20):
        data = dict(
            email='user-{:02}@{}mail.com'.format(i, domain),
            password=DEFAULT_PASSWORD
        )
        res = app.post('/user/register', data=data)
        user = json.loads((res.data.decode('utf8')))
        users.append(user)
    app.set_cookie('localhost.local', 'session', value=cookie)
    return users


def test_followers(auth_app, generated_users):
    user_ids = {_['_id'] for _ in generated_users}

    res = auth_app.get('/user/me')
    my_id = json.loads((res.data.decode('utf8')))['_id']
    for u in generated_users:
        auth_app.post('/user/{}/follow'.format(u['_id']))
    limit = 5
    loaded_user_ids = set()
    for offset in range(0, len(generated_users), limit):
        path = '/user/{}/following?offset={}&limit={}'.format(my_id, offset, limit)
        content = auth_app.get(path).data.decode('utf8')
        res = json.loads(content)
        users = res['users']
        assert len(users) <= limit
        for u in users:
            user_id = u['_id']
            assert user_id not in loaded_user_ids
            loaded_user_ids.add(user_id)
            assert user_id in user_ids


def test_following(auth_app, generated_users):
    user_ids = {_['_id'] for _ in generated_users}
    res = auth_app.get('/user/me')
    my_id = json.loads((res.data.decode('utf8')))['_id']
    for user_id in user_ids:
        path = '/user/{}/followers'.format(user_id)
        content = auth_app.get(path).data.decode('utf8')
        users = json.loads(content)['users']
        follower_user_ids = {_['_id'] for _ in users}
        assert my_id in follower_user_ids


def test_unfollow(auth_app, generated_users):
    user_ids = {_['_id'] for _ in generated_users}
    res = auth_app.get('/user/me')
    my_id = json.loads((res.data.decode('utf8')))['_id']
    unfollowed_users_id = list(user_ids)[:5]
    for user_id in unfollowed_users_id:
        res = auth_app.delete('/user/{}/follow'.format(user_id))
        assert res.status_code == 200

    path = '/user/{}/following?limit={}'.format(my_id, 1000)
    content = auth_app.get(path).data.decode('utf8')
    res = json.loads(content)
    users = res['users']
    following_user_ids = {_['_id'] for _ in users}
    assert not following_user_ids.intersection(unfollowed_users_id)
    assert following_user_ids.union(unfollowed_users_id) == user_ids

    for user_id in user_ids:
        path = '/user/{}/followers'.format(user_id)
        content = auth_app.get(path).data.decode('utf8')
        users = json.loads(content)['users']
        follower_user_ids = {_['_id'] for _ in users}
        assert (user_id in following_user_ids) ^ (my_id not in follower_user_ids)


def _get_following_user_ids(my_id, auth_app):
    path = '/user/{}/following?limit={}'.format(my_id, 1000)
    content = auth_app.get(path).data.decode('utf8')
    res = json.loads(content)
    users = res['users']
    following_user_ids = {_['_id'] for _ in users}
    return following_user_ids

def _get_current_user(auth_app):
    res = auth_app.get('/user/me')
    user = json.loads((res.data.decode('utf8')))
    return user


def test_following_amount(auth_app, generated_users):
    my_id = _get_current_user(auth_app)['_id']

    for user_id in _get_following_user_ids(my_id, auth_app):
        path = '/user/{}/follow'.format(user_id)
        auth_app.delete(path)

    assert len(_get_following_user_ids(my_id, auth_app)) == 0
    assert _get_current_user(auth_app)['following_count'] == 0
    user_ids = {_['_id'] for _ in generated_users}
    following_count = 0
    for user_id in user_ids:
        path = '/user/{}/follow'.format(user_id)
        auth_app.post(path)
        following_count += 1
    assert _get_current_user(auth_app)['following_count'] == following_count
