#!/usr/bin/env python
from pymongo import MongoClient
import os
from flask import Flask, render_template, request, jsonify
from bson.objectid import ObjectId
import json
from datetime import datetime

import pdb

app = Flask(__name__)

client = MongoClient()
db = client.fullcalendar_test


@app.route('/calendarRead', methods=['POST'])
def calendarRead():
    custom_attribute = request.form['custom_attribute']
    # pdb.set_trace()
    # format start/end as ms since epoch
    date_to_ms = lambda d: datetime.strptime(d, '%Y-%m-%d').timestamp() * 1000
    start = date_to_ms(request.form['start'])
    end = date_to_ms(request.form['end'])

    collection = db['calendar']

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
    response = jsonify(events)  # TODO: apply this globally
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/calendarUpdate', methods=['POST'])
def calendarUpdate():
    print("Received event from client:")
    event = request.get_json(force=True)
    print(request.get_json)
    # custom_attribute = request.form['custom_attribute']

    collection = db['calendar']

    # allDay is received from the POST object as a string - change to boolean
    allDay_str = request.form['allDay']
    if(allDay_str == "true"):
        event['allDay'] = True
    else:
        event['allDay'] = False

    # Convert ISO strings to python datetimes to be represented as mongoDB Dates
    # timezones not taken into consideration
    iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    event['start'] = iso_to_dt(event['start'])
    if (end is not None and end != ''):
        event['end'] = iso_to_dt(event['end'])


    # Add or update collection record, determined by whether it has an ID or not
    if 'id' in event and event['id'] != '':
        event_id = event['id']
        record_id = collection.update({'_id': event_id}, event)  # Update record
    else:
        record_id = collection.insert(event)  # Insert record

    # Return the ID of the added (or updated) calendar entry
    output = {'id': str(record_id)}


    # Output in JSON
    response = jsonify(output)
    response.headers['Access-Control-Allow-Origin', '*']  # Allows running client and server on same computer
    return response


@app.route('/calendarDelete', methods=['POST'])
def calendarDelete():
    custom_attribute = request.form['custom_attribute']
    collection = db['calendar']

    # Delete the collection record using the ID
    record_id = request.forms['id']
    if(record_id is not None and record_id != ''):
        event_id = ObjectId(record_id)
        collection.remove({'_id': event_id}) # Delete record


if __name__ == '__main__':
   app.debug = True  # updates the page as the code is saved
   HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
   PORT = int(os.environ.get('PORT', 3000))
   app.run(host='0.0.0.0', port=PORT)
