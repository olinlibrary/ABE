#!/usr/bin/env python3
"""Connect to mongodb"""
from mongoengine import *
from document_models import Event, Label
import os
import logging


if os.getenv('MONGO_URI', False):  # try env variable first
    connect(os.environ.get('MONGO_URI'))
    logging.info("Using environment variable for MongoDB URI")
elif os.path.isfile("mongo_config.py"):  # then check for config file
    import mongo_config
    if mongo_config.use_local:
        connect(mongo_config.db)
        logging.info('Using database {} on localhost'.format(mongo_config.db))
    else:
        connect(mongo_config.mongo_uri)
        logging.info("Using URI from mongo_config.py")
else:  # use localhost otherwise
    connect()
    logging.info("Using localhost with no database selected")
