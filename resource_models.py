#!/usr/bin/env python3
"""Resource models for flask"""

from flask import jsonify, request, abort, Response, make_response
from flask_restful import Resource
from mongoengine import ValidationError
from pprint import pprint, pformat
from bson import json_util, objectid
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from helpers import (
    mongo_to_dict, request_to_dict, mongo_to_ics, event_query, get_to_event_search,
    recurring_to_full, update_sub_event
    )
from icalendar import Calendar

import pdb
import requests

import logging

import database as db


class EventApi(Resource):
    """API for interacting with events"""

    def get(self, event_id=None):
        """Retrieve events"""
        if event_id:  # use event id if present
            print('eventid: ' + event_id)
            result = db.Event.objects(id=event_id).first()
            if not result:
                abort(404)

            return jsonify(mongo_to_dict(result))
        else:  # search database based on parameters

            query_dict = get_to_event_search(request)
            query = event_query(query_dict)
            results = db.Event.objects(**query)
            logging.debug('found {} events for query'.format(len(results)))
            if not results:
                abort(404)

            if 'start' in query_dict:
                start = datetime.strptime(query_dict['start'], '%Y-%m-%d')
            else:
                start = datetime(2017,7,1)
            if 'end' in query_dict:
                end = datetime.strptime(query_dict['end'], '%Y-%m-%d')
            else:
                end = datetime(2017, 7, 20)


            events_list = []
            for event in results:
                # checks for recurrent events
                if 'recurrence' in event:
                    # checks for events from a recurrence that's been edited
                    events_list = recurring_to_full(event, events_list, start, end)
                else:
                    events_list.append(mongo_to_dict(event))
            return jsonify(events_list)

    def post(self):
        """Create new event with parameters passed in through args or form"""
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))  # combines args and form
        try:
            ''' <-- implement this code for updating subevents
            iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)

            received_data['start'] = iso_to_dt(received_data['start'])

            if 'end' in received_data and received_data['end'] is not None:
                received_data['end'] = iso_to_dt(received_data['end'])

            if 'rec_id' in received_data and received_data['rec_id'] is not None:
                received_data['rec_id'] = iso_to_dt(received_data['rec_id'])

            if 'sid' in received_data and received_data['sid'] is not None:
                update_sub_event(received_data)
            else:
            '''
            new_event = db.Event(**received_data)
            new_event.save()
        except ValidationError as error:
            if request.headers['Content-Type'] == 'application/json':
                return make_response(jsonify({
                    'error_type': 'validation',
                    'validation_errors': [str(err) for err in error.errors],
                    'error_message': error.message}),
                    400
                )
            else:
                return make_response(
                    'Validation Error\n{}'.format(error),
                    400
                )
        else:  # return success
            if request.headers['Content-Type'] == 'application/json':
                return make_response(
                    jsonify(mongo_to_dict(new_event)),
                    201
                )
            else:
                return make_response(
                    "Event Created\n{}".format(
                        pformat(mongo_to_dict(new_event))
                    ),
                    201,
                    {'Content-Type': 'text'}
                )

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
            return jsonify({'id': str(new_event.id)}), 201


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
