#!/usr/bin/env python
from pymongo import MongoClient
import os
import random
from flask import Flask, render_template, request, jsonify, make_response, Response
from bson.objectid import ObjectId
from bson import json_util
from datetime import datetime, timedelta

import logging
FORMAT = "%(levelname)s:ABE: _||_ %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

import pdb

from icalendar import Calendar, Event, vCalAddress, vText
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY, HOURLY, MINUTELY
import dateutil.parser
import json

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
    "name": "rec-test",  # name of database
    "events_collection": "calendar",  # collection that holds events
}

db = client[db_setup['name']]
'''ics_database = {
    {
        'title':'Book Club',
        'location': 'Quiet Reading Room',
        'description': 'reading cool books',
        'start': ISODate("2017-06-19T15:00:00Z"),
        'end': ISODate("2017-06-19T16:00:00Z"),
        'endrecurrence' : ISODate("2017-07-31"),
        'UID' : '20170619150000-456',
        'recurrence' : {
            'frequency' : 'WEEKLY',
            'interval' : '1',
            'count' : '7',
            'BYDAY' : "MO"
            }
    },
    {
        'title':'Newsch Celebration',
        'location': 'Library',
        'description': 'Doing cool newsch things',
        'start': ISODate("2017-06-21T15:00:00Z"),
        'end': ISODate("2017-06-21T16:00:00Z"),
        'endrecurrence' : ISODate("2017-07-12"),
        'UID' : '20170619160000-780',
        'recurrence' : {
            'frequency' : 'WEEKLY',
            'interval' : '1',
            'count' : '4',
            'BYDAY' : "WE"
            }
    },
}'''

def create_calendar(events):
    #initialize calendar object
    cal = Calendar()
    for event in events:
        new_event = Event()
        new_event.add('summary', event['title'])
        new_event.add('location', event['location'])
        new_event.add('description', event['description'])
        new_event.add('dtstart', event['start'])
        if event['end'] is not None:
            new_event.add('dtend', event['end'])

        #event.find({""})
        recurrence = event['recurrence']
        if recurrence:
            rec_ics_string = {}
            frequency = recurrence['frequency']
            interval = recurrence['interval']
            rec_ics_string['freq'] = frequency
            rec_ics_string['interval'] = interval

            if 'until' in recurrence:
                rec_ics_string['until'] = reccurrence['until']
            elif 'count' in recurrence:
                rec_ics_string['count'] = recurrence['count']

            if frequency == 'WEEKLY':
                rec_ics_string['byday'] = recurrence['BYDAY']

            if frequency == 'MONTHLY':
                if recurrence['BYDAY']:
                    rec_ics_string['byday'] = recurrence['BYDAY']
                elif recurrence['BYMONTHDAY']:
                    rec_ics_string['bymonthday'] = recurrence['BYMONTHDAY']

            if frequency == 'YEARLY':
                if recurrence['BYMONTH']:
                    rec_ics_string['bymonth'] = recurrence['BYMONTH']
                elif recurrence['BYYEARDAY']:
                    rec_ics_string['byday'] = recurrence['BYDAY']

            new_event.add('RRULE', rec_ics_string)

        new_event.add('TRANSP', 'OPAQUE')

        #str(iso_to_dt(str(datetime.now())))
        iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        uid = str(iso_to_dt(str(datetime.now().isoformat())))+'-'+str(random.randint(0,10000000))
        new_event.add('UID', uid)
        #vevent.add('attendee', 'MAILTO:emily.lepert@gmail.com')

        cal.add_component(new_event)


    response = cal.to_ical()
    return response

def pseudo_calendarRead():
    date_to_dt = lambda d: datetime.strptime(d, '%Y-%m-%d')

    start = datetime(2017,6,1)
    end = datetime(2017, 7, 1)

    collection = db[db_setup['events_collection']]

    events = []

    # Ensure there is an index on start date
    collection.ensure_index([('start', 1)])

    # Fetch the event objects from MongoDB
    recs = collection.find({ 
        '$or': [
            {'start':{'$gte': start, '$lte': end}}, 
            { '$and' : [
                {'endrecurrence': {'$gte': start}}, 
                {'start' : {'$lte' : end}}
            ]}
        ]
    }) # Can add filter here for customer or calendar ID, etc
    
    for rec in recs:
        event = rec
        # Replace the ID with its string version, since the object is not serializable this way
        event['id'] = str(rec['_id'])
        del(event['_id'])

        event_end = datetime.strptime(str(event['end']), "%Y-%m-%d %H:%M:%S")
        event_start = datetime.strptime(str(event['start']), "%Y-%m-%d %H:%M:%S")

        if 'recurrence' in event:
            if 'sub_events' in event:
                for sub_event in event['sub_events']:
                    if sub_event['start'] <= end and sub_event['end'] >= start:
                        events.append(sub_event)


            recurrence = event['recurrence']
            if recurrence['frequency'] == 'YEARLY':
                rFrequency = 0
            elif recurrence['frequency'] == 'MONTHLY':
                rFrequency = 1
            elif recurrence['frequency'] == 'WEEKLY':
                rFrequency = 2
            elif recurrence['frequency'] == 'DAILY':
                rFrequency = 3

            rInterval = recurrence['interval']
            rCount = recurrence['count'] if 'count' in recurrence else None
            rUntil = recurrence['until'] if 'until' in recurrence else None
            rByMonth = recurrence['BYMONTH'] if 'BYMONTH' in recurrence else None
            rByMonthDay = recurrence['BYMONTHDAY'] if 'BYMONTHDAY' in recurrence else None
            rByDay = recurrence['BYDAY'] if 'BYDAY' in recurrence else None

            
            rule_list = list(rrule(freq=rFrequency, count=int(rCount), interval=int(rInterval), until=rUntil, bymonth=rByMonth, \
                bymonthday=rByMonthDay, byweekday=None, dtstart=event['start']))

            for instance in rule_list:
                print(instance)
                if instance >= start and instance < end:
                    instance = datetime.strptime(str(instance), "%Y-%m-%d %H:%M:%S")
                    
                    repeat = False
                    if 'sub_events' in event:
                        for individual in event['sub_events']:
                            indiv = datetime.strptime(str(individual['recurrence-id']), "%Y-%m-%dT%H:%M:%SZ")
                            print('-------------')
                            print(instance)
                            print(indiv)
                            print('-------------')

                            if instance == indiv:
                                repeat = True

                    if repeat == False:
                        fake_object = {}
                        fake_object['title'] = event['title']
                        fake_object['location'] = event['location']
                        fake_object['description'] = event['description']
                        fake_object['start'] = instance
                        fake_object['end'] = (event_end-event_start+instance)
                        fake_object['UID'] = event['UID']
                        events.append(json.dumps(fake_object, default=json_util.default))
        else:
            events.append(event)

    # outputStr = json.dumps(events)
    # pdb.set_trace()
    logging.debug("Found {} events for start {} and end {}".format(len(events), start, end))
    #response = jsonify(events)  # TODO: apply this globally
    #response.headers.add('Access-Control-Allow-Origin', '*')
    return events

def pseudo_calendarUpdate():
    event = {
        'id': ObjectId('59497c0b93732a1ae3dfe12c'),
        'title':'Newsch Celebration',
        'location': 'Library',
        'description': 'Doing cool newsch things',
        'start': "2017-06-21T13:00:00Z",
        'end': "2017-06-21T14:00:00Z",
        'recurrence-id' : "2017-06-21T15:00:00Z",
    }

    collection = db[db_setup['events_collection']]
    calendar = collection.find({})


    # Convert ISO strings to python datetimes to be represented as mongoDB Dates
    # timezones not taken into consideration
    # TODO: have frontend format dates correctly
    iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
    event['start'] = iso_to_dt(event['start'])
    if 'end' in event and event['end'] is not None:
        event['end'] = iso_to_dt(event['end'])

    # Add or update collection record, determined by whether it has an ID or not
    if 'id' in event and event['id'] is not None:
        
        current_rec = collection.find({'_id': event['id']})

        if 'recurrence-id' in event:
            collection.update({ '_id' : event['id']}, {'$push': {'sub_events' : event}})
        else:
            record_id = collection.update({'id': event['id']}, event)  # Update record
        #logging.debug("Updated entry with id {}".format(record_id))
    else:
        record_id = collection.insert(event)  # Insert record
        logging.debug("Added entry with id {}".format(record_id))

        

    # Return the ID of the added (or updated) calendar entry
    #output = {'id': str(record_id)}
   
    # pdb.set_trace()
    # Output in JSON
    #response = jsonify(db)
    responses = db.calendar.find({})
    #response.headers.add('Access-Control-Allow-Origin', '*')  # Allows running client and server on same computer
    return [response for response in responses]

print(pseudo_calendarRead())

@app.route('/icsFeed/<username>')
def icsFeed(username):
    collection = db['calendar']
    events = collection.find({}) # Can add filter here for customer or calendar ID, etc
    response = create_calendar(events)
    cd = "attachment;filename="+username+".ics"
    return Response(response,
                       mimetype="text/calendar",
                       headers={"Content-Disposition": cd})


@app.route('/icsFeed/label/<label>') #, methods=['GET', 'POST']
def label_icsFeed(label):
    collection = db['calendar']
    events = collection.find({'labels':label}) # Can add filter here for customer or calendar ID, etc
    response = create_calendar(events)
    cd = "attachment;filename="+label+".ics"
    return Response(response,
                       mimetype="text/calendar",
                       headers={"Content-Disposition": cd})


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

event = {
    "title" : "Friday Funday",

}




if __name__ == '__main__':
   app.debug = True  # updates the page as the code is saved
   HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
   PORT = int(os.environ.get('PORT', 3000))
   app.run(host='0.0.0.0', port=PORT)
