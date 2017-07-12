#!/usr/bin/env python3
"""Script used to drop databases for Heroku review apps after closing"""
import logging
logging.basicConfig(level=logging.DEBUG)
import os
from pymongo import MongoClient

logging.info('Performing predestroy process')
db_name = os.getenv('HEROKU_APP_NAME', None)
if db_name:
    logging.warning('Dropping db {}'.format(db_name))
    from database import mongo_uri, mongo_db_name
    client = MongoClient(mongo_uri)  # use pymongo to drop database
    client.drop_database(db_name)
    client.close()
else:
    logging.info('No env variable found with name "DB_NAME"')
logging.info('Finished predestroy process')
