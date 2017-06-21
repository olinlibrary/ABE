#!/usr/bin/env python3
"""Resource models for flask"""
from flask import Flask, jsonify, render_template, request, abort
from flask_restful import Resource, Api, reqparse
from flask_restful.utils import cors
from flask_cors import CORS, cross_origin
from pprint import pprint, pformat
from bson import json_util
from datetime import datetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY, HOURLY, MINUTELY
import json
import os
import isodate
import logging

import database as db


class EventApi(Resource):
    """API for interacting with events"""

    @cors.crossdomain(origin='*')
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

            return jsonify(json.loads(result.to_json()))
        else:  # search database based on parameters
            # TODO: search based on parameters
            results = db.Event.objects(__raw__={ 
                '$or': [
                    {'start':{'$gte': start, '$lte': end}}, 
                    { '$and' : [
                        {'endrecurrence': {'$gte': start}}, 
                        {'start' : {'$lte' : end}}
                    ]}
                ]
            })
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

    @cors.crossdomain(origin='*')
    def post(self):
        """Create new event with parameters passed in through args or form"""
        print('***REQUEST DATA***\n' + request.data)
        received_data = dict(request.data)  # combines args and form
        try:
            new_event = db.Event(**received_data)
            new_event.save()
        except Exception as error:
            abort(400)

        return "", 201

    @cors.crossdomain(origin='*')
    def put(self, event_id):
        """Replace individual event"""
        pass

    @cors.crossdomain(origin='*')
    def patch(self, event_id):
        """Modify individual event"""
        pass

    @cors.crossdomain(origin='*')
    def delete(self, event_id):
        """Delete individual event"""
        pass


class LabelApi(Resource):
    """API for interacting with all labels (searching, creating)"""

    @cors.crossdomain(origin='*')
    def get(self, label_name=None):
        """Retrieve labels"""
        if label_name:  # use event id if present
            result = db.Label.objects(name=label_name).first()
            if not result:
                abort(404)
            else:
                return jsonify(json.loads(result.to_json()))
        else:  # search database based on parameters
            # TODO: search based on terms
            results = db.Label.objects()
            if not results:
                abort(404)
            else:
                return jsonify([json.loads(result.to_json()) for result in results])

    @cors.crossdomain(origin='*')
    def post(self):
        """Create new label with parameters passed in through args or form"""
        print('***REQUEST DATA***\n' + request.data)
        received_data = dict(request.data)  # combines args and form
        try:
            new_label = db.Label(**received_data)
            new_label.save()
        except ValidationError as error:
            abort(400)

        return 201

    @cors.crossdomain(origin='*')
    def put(self, label_name):
        """Replace individual event"""
        pass

    @cors.crossdomain(origin='*')
    def patch(self, label_name):
        """Modify individual event"""
        pass

    @cors.crossdomain(origin='*')
    def delete(self, label_name):
        """Delete individual event"""
        pass
