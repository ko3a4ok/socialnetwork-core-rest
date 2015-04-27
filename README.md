REST API for social network template
===============

Uses: (flask, mongo, redis)

API:
----
* `/user/register` - POST method; register new user. parameters: email, password
* `/user/login` - POST method; login user. parameters: email, password. returns User info and access_token
* `/user/find?q=UserName&limit=<Size>&offset=<Size>` - GET method; find users
* `/user/<id>` - GET method; return info about user with user_id
* `/user/me` - GET/POST method; get and update own profile

