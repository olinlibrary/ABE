#!/usr/bin/env python
from pymongo import MongoClient
import os
from flask import Flask, render_template, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime, timedelta

import logging
FORMAT = "%(levelname)s:ABE: _||_ %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

import pdb

app = Flask(__name__)

# connect to MongoDB
if os.getenv('MONGO_URI', False):  # try env variable first
    client = MongoClient(os.environ.get('MONGO_URI'))
    logging.info("Using environment variable for MongoDB URI")
elif os.path.isfile("mongo_config.py"):  # then check for config file
    import mongo_config
    if mongo_config.use_local:
        client = MongoClient()
        logging.info("Using localhost for MongoDB URI")
    else:
        client = MongoClient(mongo_config.mongo_uri)
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
def splash():
    return render_template('splash.html')


@app.route('/calendarRead', methods=['POST'])
def calendarRead():
    # pdb.set_trace()
    # format start/end as ms since epoch

    date_to_dt = lambda d: datetime.strptime(d, '%Y-%m-%d')

    start = date_to_dt(request.form['start'])
    end = date_to_dt(request.form['end'])

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
    event = request.get_json(force=True)
    logging.debug("Received event from client: {}".format(event))

    collection = db[db_setup['events_collection']]

    # # allDay is received from the POST object as a string - change to boolean
    # allDay_str = event['allDay']
    # if(allDay_str == "true"):
    #     event['allDay'] = True
    # else:
    #     event['allDay'] = False

    # Convert ISO strings to python datetimes to be represented as mongoDB Dates
    # timezones not taken into consideration
    # TODO: have frontend format dates correctly
    iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(hours=4)
    event['start'] = iso_to_dt(event['start'])
    if 'end' in event and event['end'] is not None:
        event['end'] = iso_to_dt(event['end'])

    # Add or update collection record, determined by whether it has an ID or not
    if 'id' in event and event['id'] is not None:
        event_id = event['id']
        record_id = collection.update({'_id': event_id}, event)  # Update record
        logging.debug("Updated entry with id {}".format(record_id))
    else:
        record_id = collection.insert(event)  # Insert record
        logging.debug("Added entry with id {}".format(record_id))

    # Return the ID of the added (or updated) calendar entry
    output = {'id': str(record_id)}
    print('neat')
    # pdb.set_trace()
    # Output in JSON
    response = jsonify(output)
    response.headers.add('Access-Control-Allow-Origin', '*')  # Allows running client and server on same computer
    return response


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
