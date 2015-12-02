REST API for social network template
===============

Uses: (flask, mongo, redis)

API:
----
* `/user/register` - POST method; register new user. parameters: email, password
* `/user/login` - POST method; login user. parameters: email, password. returns User info and access_token
* `/user/facebook` - POST method; login/register facebook's user. parameters: access_token. returns User info and access_token
* `/user/find?q=UserName&limit=<Size>&offset=<Size>` - GET method; find users
* `/user/<id>` - GET method; return info about user with user_id
* `/user/me` - GET/POST methods; get and update own profile
* `/user/<id>/follow` - POST/DELETE methods; follow and unfollow user
* `/user/<id>/follower?limit=<Size>&offset=<Size>` - GET method; return list of user's followers
* `/user/<id>/following?limit=<Size>&offset=<Size>` - GET method; return list of user's following

* `/post` - POST method; create new user post
* `/user/me/post/<post_id>` - PUT/DELETE methods; change or remove user post
* `/post/<post_id>` - GET method; get user's post by id
* `/timeline/<user_id>?limit=<Size>&before=<post_id>` - GET method; get user posts
* `/feed?limit=<Size>&before=<post_id>` - GET method; get current and following users' posts
* `/post/<post_id>/like` - POST/DELETE methods; add or remove like for user post
* `/post/<post_id>/like?limit=<Size>&offset=<Size>` - GET method; return list of users who like this post
* `/post/<post_id>/comment` - POST method; add comment to the user post
* `/post/<post_id>/comment/<comment_id>` - PUT/DELETE method; change or remove comment
* `/post/<post_id>/comment?limit=<Size>&offset=<Size>` - GET method; return list of comments for this post

