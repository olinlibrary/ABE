#!/usr/bin/env python3
"""Resource models for flask"""

from flask import jsonify, request, abort, Response, make_response
from flask_restful import Resource
from mongoengine import ValidationError
from bson.objectid import ObjectId
from pprint import pprint, pformat
from bson import json_util, objectid
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from helpers import (
    mongo_to_dict, request_to_dict, mongo_to_ics, event_query, get_to_event_search,
    recurring_to_full, update_sub_event
    )
from icalendar import Calendar

from helpers import *

import pdb
import requests

import logging

import database as db


class EventApi(Resource):
    """API for interacting with events"""

    def get(self, event_id=None, rec_id=None):
        """Retrieve events"""
        #for i in db.Event.objects({}):
            #logging.debug("showing entire database {}".format(mongo_to_dict(i)))
        if event_id:  # use event id if present
            logging.debug('Event requested: ' + event_id)
            result = db.Event.objects(id=event_id).first()
            if not result:
                cur_parent_event = db.Event.objects(__raw__ = {'sub_events._id' : objectid.ObjectId(event_id)}).first()
                if cur_parent_event:
                    cur_sub_event = access_sub_event(mongo_to_dict(cur_parent_event),objectid.ObjectId(event_id))
                    logging.debug("cur_sub_event: {}".format(cur_sub_event))
                    return jsonify(sub_event_to_full(cur_sub_event,cur_parent_event))
                else:
                    logging.debug("No sub_event found")
                    abort(404)
            elif rec_id:
                logging.debug('Sub_event requested: ' + rec_id)
                result = placeholder_recurring_creation(rec_id, [], result, True)
                if not result:
                    logging.debug("No dummy object created with rec_id")
                    abort(404)
                return jsonify(result)
            else:
                logging.debug("No event or sub_event found. No rec_id sent.")
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
                start = datetime(2017,6,1)
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
            new_event = db.Event(**received_data)
            if new_event.labels == []:
                new_event.labels = ['unlabeled']
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
        """Modify individual event"""
        logging.debug('Editing event with id: ' + event_id)


        received_data = request_to_dict(request)
        logging.debug("Received PUT data: {}".format(received_data))
        try:
            result = db.Event.objects(id=event_id).first()
            if not result:
                cur_sub_event = db.Event.objects(__raw__ = {'sub_events._id' : objectid.ObjectId(event_id)})
                if cur_sub_event:
                    update_sub_event(received_data,result, cur_sub_event, False)
                else:
                    abort(404)
            else:
                if 'sid' in received_data and received_data['sid'] is not None:
                    iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)

                    if 'rec_id' in received_data and received_data['rec_id'] is not None:
                        received_data['rec_id'] = dateutil.parser.parse(str(received_data['rec_id']))
                        update_sub_event(received_data, result)
                else:
                    result.update(**received_data)
        except ValidationError as error:
            if 'application/json' in request.headers['Content-Type']:
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
            if 'application/json' in request.headers['Content-Type']:
                return make_response(
                    jsonify(mongo_to_dict(result)),
                    200
                )
            else:
                return make_response(
                    "Event Updated\n{}".format(
                        pformat(mongo_to_dict(result))
                    ),
                    200,
                    {'Content-Type': 'text'}
                )


    def delete(self, event_id):
        """Delete individual event"""
        logging.debug('Event requested: ' + event_id)
        result = db.Event.objects(id=event_id).first()
        if not result:
            abort(404)

        received_data = request_to_dict(request)
        logging.debug("Received DELETE data: {}".format(received_data))
        result.delete()
        if 'application/json' in request.headers['Content-Type']:
            return make_response(
                jsonify(mongo_to_dict(result)),
                200
            )
        else:
            return make_response(
                "Event Deleted\n{}".format(
                    pformat(mongo_to_dict(result))
                ),
                200,
                {'Content-Type': 'text'}
            )


class LabelApi(Resource):
    """API for interacting with all labels (searching, creating)"""


    def get(self, label_name=None):
        """Retrieve labels"""
        if label_name:  # use label name/object id if present
            logging.debug('Label requested: ' + label_name)
            search_fields = ['name', 'id']
            result = multi_search(db.Label, label_name, search_fields)
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
            new_label = db.Label(**received_data)
            new_label.save()
        except ValidationError as error:
            logging.warning("POST request rejected: {}".format(str(error)))
            return error, 400
        else:  # return success
            return jsonify({'id': str(new_label.id)}), 201


    def put(self, label_name):
        """Modify individual label"""
        logging.debug('Label requested: ' + label_name)
        search_fields = ['name', 'id']
        result = multi_search(db.Label, label_name, search_fields)
        if not result:
            abort(404)

        try:
            result.update(**received_data)
        except ValidationError as error:
            if 'application/json' in request.headers['Content-Type']:
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
            if 'application/json' in request.headers['Content-Type']:
                return make_response(
                    jsonify(mongo_to_dict(result)),
                    200
                )
            else:
                return make_response(
                    "Label Updated\n{}".format(
                        pformat(mongo_to_dict(result))
                    ),
                    200,
                    {'Content-Type': 'text'}
                )

    def delete(self, label_name):
        """Delete individual label"""
        logging.debug('Label requested: ' + label_name)
        search_fields = ['name', 'id']
        result = multi_search(db.Label, label_name, search_fields)
        if not result:
            abort(404)

        received_data = request_to_dict(request)
        logging.debug("Received DELETE data: {}".format(received_data))
        result.delete()
        if 'application/json' in request.headers['Content-Type']:
            return make_response(
                jsonify(mongo_to_dict(result)),
                200
            )
        else:
            return make_response(
                "Event Deleted\n{}".format(
                    pformat(mongo_to_dict(result))
                ),
                200,
                {'Content-Type': 'text'}
            )


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