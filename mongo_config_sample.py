#!/usr/bin/env python
"""Configuration for MongoDB

app.py first checks if mongo_config.py exists, then connects with the default
localhost setup if use_local is True. If use_local is False, it connects to
MongoDB with the mongo_uri string.

https://docs.mongodb.com/manual/reference/connection-string/
"""

mongodb_options = {
    "username": "fred",
    "password": "fluffy stoic cactus",
    "host": "localhost",
    "port": "27017",  # default mongodb port
}

uri_format = 'mongodb://{username}:"{password}"@{host}:{port}'

mongo_uri = uri_format.format(**mongodb_options)
db = 'testing'  # name of database to use, overridden by uri
use_local = False  # ignore the uri and use locally hosted mongodb instance
