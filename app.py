#!/usr/bin/env python
from pymongo import MongoClient
import os
from flask import Flask, render_template, request, jsonify
from bson.objectid import ObjectId
import json
from datetime import datetime
import importlib

import logging
FORMAT = "%(levelname)s:ABE: _||_ %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

import pdb

app = Flask(__name__)

# connect to MongoDB
if os.getenv('MONGO_URI', False):  # use env variable first
    client = MongoClient(os.environ.get('MONGO_URI'))
    logging.info("Using environment variable for MongoDB URI")
elif os.path.isfile("mongo_config.py"):  # then check for config file
    from mongo_config import mongo_uri
    client = MongoClient(mongo_uri)
    logging.info("Using config file for MongoDB URI")
else:  # use localhost otherwise
    client = MongoClient()
    logging.info("Using localhost for MongoDB URI")

# Database organization
db_setup = {
    "name": "backend-testing",  # name of database
    "events_collection": "calendar",  # collection that holds events
}

db = client[db_setup['name']]


@app.route('/')
def welcomePage():
    return render_template('index.html')


@app.route('/calendarRead', methods=['POST'])
def calendarRead():
    custom_attribute = request.form['custom_attribute']
    # pdb.set_trace()
    # format start/end as ms since epoch

    date_to_ms = lambda d: datetime.strptime(d, '%Y-%m-%d').timestamp() * 1000

    start = date_to_ms(request.form['start'])
    end = date_to_ms(request.form['end'])

    collection = db[db_setup['events_collection']]

    events = []

    # Ensure there is an index on start date
    collection.ensure_index([('start', 1)])

    # Fetch the event objects from MongoDB
    recs = collection.find({'start':{'$gte': start, '$lte': end}}) # Can add filter here for customer or calendar ID, etc

    for rec in recs:
        event = rec

        # Replace the ID with its string version, since the object is not serializable this way
        event['id'] = str(rec['_id'])
        del(event['_id'])

        events.append(event)

    # outputStr = json.dumps(events)
    # pdb.set_trace()
    logging.debug("Found {} events for start {} and end {}".format(len(events), request.form['start'], request.form['end']))
    response = jsonify(events)  # TODO: apply this globally
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/calendarUpdate', methods=['POST'])
def calendarUpdate():
    custom_attribute = request.form['custom_attribute']

    collection = db[db_setup['events_collection']]

    event = {}
    event['title'] = request.form['title']

    # allDay is received from the POST object as a string - change to boolean
    allDay_str = request.form['allDay']
    if(allDay_str == "true"):
        event['allDay'] = True
    else:
        event['allDay'] = False

    # We're receiving dates in ms since epoch, so divide by 1000
    event['start'] = int(request.form['start'])/1000

    # Set end-date if it exists
    end = request.form['end']
    if (end is not None and end != ''):
        event['end'] = int(end)/1000

    # Set entry colour if it exists
    color = request.form['color']
    if (color is not None and color != ''):
        event['color'] = request.form['color']

    # Add or update collection record, determined by whether it has an ID or not
    record_id = request.form['id']
    if(record_id is not None and record_id != ''):
        event_id = ObjectId(record_id)
        collection.update({'_id': event_id}, event) # Update record
    else:
        record_id = collection.insert(event) # Insert record

    # Return the ID of the added (or updated) calendar entry
    output = {}
    output['id'] = str(record_id)
    logging.debug("Added/Updated entry {}".format(output["id"]))

    # Output in JSON
    outputStr = json.dumps(output)
    return render_template('{{!output}}', output=outputStr)

@app.route('/calendarDelete', methods=['POST'])
def calendarDelete():
    custom_attribute = request.form['custom_attribute']
    collection = db[db_setup['events_collection']]

    # Delete the collection record using the ID
    record_id = request.forms['id']
    if(record_id is not None and record_id != ''):
        event_id = ObjectId(record_id)
        collection.remove({'_id': event_id}) # Delete record
        logging.debug("Deleted entry {}".format(output["id"]))


if __name__ == '__main__':
   app.debug = True  # updates the page as the code is saved
   HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
   PORT = int(os.environ.get('PORT', 3000))
   app.run(host='0.0.0.0', port=PORT)
