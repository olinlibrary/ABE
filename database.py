#!/usr/bin/env python3
"""Connect to mongodb"""
from mongoengine import *
from document_models import Event, Label, RecurringEventExc
import os
import logging

config_present = os.path.isfile("mongo_config.py")
env_present = os.environ.get('MONGO_URI')
if config_present:
    from mongo_config import mongo_uri, use_local, db_name
else:
    use_local = False
    uri = None
    db_name = None
mongo_uri = os.getenv('MONGO_URI', uri) if not use_local else None
mongo_db_name = os.getenv('DB_NAME', db_name)

connect(mongo_db_name, host=mongo_uri)

if env_present:
    location = 'uri from environment variable'
elif config_present and not use_local:
    location = 'uri from config file'
else:
    location = 'localhost'

logging.info('Using db "{}" with {}'.format(mongo_db_name, location))

