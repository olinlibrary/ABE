#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script used to create databases for Heroku review apps"""
import logging
logging.basicConfig(level=logging.DEBUG)
import os
from sample_data import load_data
from pymongo import MongoClient

import pdb

logging.info('Performing postdeploy process')
db_name = os.getenv("HEROKU_APP_NAME", "testing")
logging.warning('Dropping db "{}"'.format(db_name))
from database import mongo_uri, mongo_db_name
client = MongoClient(mongo_uri)  # use pymongo to drop database
client.drop_database(db_name)
client.close()
logging.warning('Filling db "{}" with sample data'.format(db_name))
import database as db
load_data(db)  # fill database with mongoengine
logging.info('Finished postdeploy process')
