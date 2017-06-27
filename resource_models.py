#!/usr/bin/env python3
"""Resource models for flask"""
from flask import Flask, jsonify, render_template, request, abort, Response
from flask_restful import Resource, Api, reqparse
from flask_restful.utils import cors
from flask_cors import CORS, cross_origin
from pprint import pprint, pformat
from bson import json_util, objectid
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY, HOURLY, MINUTELY
from helpers import mongo_to_dict, request_to_dict, mongo_to_ics, event_query, get_to_event_search
import json
import os
import isodate
import pdb
from mongoengine import ValidationError
import requests
from icalendar import Calendar
import logging

import database as db


class EventApi(Resource):
    """API for interacting with events"""

    def get(self, event_id=None):
        date_to_dt = lambda d: datetime.strptime(d, '%Y-%m-%d')
        
        if request.form:
            start = date_to_dt(request.form['start'])
            end = date_to_dt(request.form['end'])
        else:
            start = datetime(2017,6,1)
            end = datetime(2017, 7, 20)

        """Retrieve events"""
        if event_id:  # use event id if present
            print('eventid: ' + event_id)
            result = db.Event.objects(id=event_id).first()
            if not result:
                abort(404)

            return jsonify(mongo_to_dict(result))
        else:  # search database based on parameters
            query = event_query(get_to_event_search(request))
            results = db.Event.objects(**query)
            logging.debug('found {} events for query'.format(len(results)))
            if not results:
                abort(404)

            
            events = []
            for rec in results:
                event = rec
                # Replace the ID with its string version, since the object is not serializable this way
                event['id'] = str(rec['id'])
                #del(event['id'])
                # checks for recurrent events
                if 'recurrence' in event:
                    # checks for events from a recurrence that's been edited
                    if 'sub_events' in event:
                        for sub_event in event['sub_events']:
                            if sub_event['start'] <= end and sub_event['start'] >= start:
                                events.append(sub_event)


                    recurrence = event.recurrence
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

                    event_end = datetime.strptime(str(event['end']), "%Y-%m-%d %H:%M:%S")
                    event_start = datetime.strptime(str(event['start']), "%Y-%m-%d %H:%M:%S")

                    for instance in rule_list:
                        if instance >= start and instance < end:
                            instance = datetime.strptime(str(instance), "%Y-%m-%d %H:%M:%S")
                            
                            repeat = False
                            if 'sub_events' in event:
                                for individual in event['sub_events']:
                                    indiv = datetime.strptime(str(individual['recurrence-id']), "%Y-%m-%dT%H:%M:%SZ")
                                    if instance == indiv:
                                        repeat = True

                            if repeat == False:
                                fake_object = {}
                                fake_object['title'] = event['title']
                                fake_object['location'] = event['location']
                                fake_object['description'] = event['description']
                                fake_object['start'] = isodate.parse_datetime(instance.isoformat())
                                fake_object['end'] = isodate.parse_datetime((event_end-event_start+instance).isoformat())  #.isoformat()
                                fake_object['id'] = event['id']
                                events.append(fake_object) #json.dumps(fake_object, default=json_util.default))
                else:
                    events.append(dict(event.to_mongo()))

            # TODO: fix dict to json conversion (ObjectIDs)
            return json_util.dumps(events) #result=[json.loads(result.to_json()) for result in events])

    def post(self):
        """Create new event with parameters passed in through args or form"""
        event = request_to_dict(request)
        logging.debug("Received POST data: {}".format(event))  # combines args and form
        try:
            iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
            
            event['start'] = iso_to_dt(event['start'])
            
            if 'end' in event and event['end'] is not None:
                event['end'] = iso_to_dt(event['end'])

            if 'rec_id' in event and event['rec_id'] is not None:
                event['rec_id'] = iso_to_dt(event['rec_id'])
            
            if 'sid' in event and event['sid'] is not None:
                if 'rec_id' in event:
                    rec_event = db.RecurringEventExc(**event)
                          
                    record_id = db.Event.objects(__raw__={'_id': objectid.ObjectId(event['sid'])})
            
                    cur_sub_event = db.Event.objects(__raw__ = { '$and' : [
                        {'_id': objectid.ObjectId(event['sid'])}, 
                        {'sub_events.rec_id' : event['rec_id']}]})

                    if cur_sub_event:
                        cur_sub_event.update(set__sub_events__S=rec_event)
                    else:
                        record_id.update(add_to_set__sub_events=rec_event)
                    
                    logging.debug("Updated reccurence with event with id {}".format(record_id))
                else:
                    #record_id = db.Event.objects(id=event['id']).update(inc__id__S=event)  # Update record
                    logging.debug("Updated entry with id {}".format(record_id))
            else:

                record_id = db.Event(**event).save()  # Insert record
                logging.debug("Added entry with id {}".format(record_id))

        except ValidationError as error:
            logging.warning("POST request rejected: {}".format(str(error)))
            return error, 400

        else:  # return success
            return str(new_event.id), 201

    def put(self, event_id):
        """Replace individual event"""
        pass

    def patch(self, event_id):
        """Modify individual event"""
        pass


    def delete(self, event_id):
        """Delete individual event"""
        pass


class LabelApi(Resource):
    """API for interacting with all labels (searching, creating)"""


    def get(self, label_name=None):
        """Retrieve labels"""
        if label_name:  # use event id if present
            result = db.Label.objects(name=label_name).first()
            if not result:
                abort(404)
            else:

                return jsonify(mongo_to_dict(result))
        else:  # search database based on parameters
            # TODO: search based on terms
            results = db.Label.objects()
            if not results:
                abort(404)
            else:
                return jsonify([mongo_to_dict(result) for result in results])

    def post(self):
        """Create new label with parameters passed in through args or form"""
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))
        try:
            new_event = db.Label(**received_data)
            # pdb.set_trace()
            new_event.save()
        except ValidationError as error:
            logging.warning("POST request rejected: {}".format(str(error)))
            return error, 400
        else:  # return success
            return str(new_event.id), 201


    def put(self, label_name):
        """Replace individual event"""
        pass

    def patch(self, label_name):
        """Modify individual event"""
        pass

    def delete(self, label_name):
        """Delete individual event"""
        pass


class ICSFeed(Resource):

    def get(self, ics_name=None):
        if ics_name:
            # configure ics specs from fullcalendar to be mongoengine searchable
            query = event_query(get_to_event_search(request))
            results = db.Event.objects(**query)
            response = mongo_to_ics(results)
            cd = "attachment;filename="+ics_name+".ics"
            return Response(response,
                       mimetype="text/calendar",
                       headers={"Content-Disposition": cd})



    def post(self):
        #reads outside ics feed
        url = request_to_dict(request)
        data = requests.get(url['url'].strip()).content.decode('utf-8')
        cal = Calendar.from_ical(data)
        
        for component in cal.walk():
            if component.name == "VEVENT":
                print(component.get('summary'))
                print(component.get('dtstart'))
                print(component.get('dtend'))
                print(component.get('dtstamp'))

    def put(self, ics_name):
        pass

    def patch(self, ics_name):
        pass

    def delete(self, ics_name):
        pass

    