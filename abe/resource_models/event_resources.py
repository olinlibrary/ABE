#!/usr/bin/env python3
"""Event Resource models for flask"""

from flask import jsonify, request, abort, Response, make_response
from flask_restful import Resource
from mongoengine import ValidationError
from bson.objectid import ObjectId
from pprint import pprint, pformat
from bson import json_util, objectid
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from icalendar import Calendar
import isodate

import pdb
import requests

import logging

from abe import database as db
from abe.helper_functions.converting_helpers import request_to_dict, mongo_to_dict
from abe.helper_functions.recurring_helpers import recurring_to_full, placeholder_recurring_creation
from abe.helper_functions.sub_event_helpers import create_sub_event, update_sub_event, sub_event_to_full, access_sub_event, find_recurrence_end
from abe.helper_functions.query_helpers import get_to_event_search, event_query


class EventApi(Resource):
    """API for interacting with events"""

    def get(self, event_id=None, rec_id=None):
        """Retrieve events"""

        if event_id:  # use event id if present
            logging.debug('Event requested: ' + event_id)
            result = db.Event.objects(id=event_id).first()

            if not result:
                cur_parent_event = db.Event.objects(__raw__ = {'sub_events._id' : objectid.ObjectId(event_id)}).first()
                if cur_parent_event:
                    cur_sub_event = access_sub_event(mongo_to_dict(cur_parent_event),objectid.ObjectId(event_id))
                    return sub_event_to_full(cur_sub_event,cur_parent_event)
                else:
                    logging.debug("No sub_event found")
                    abort(404)
            elif rec_id:
                logging.debug('Sub_event requested: ' + rec_id)
                result = placeholder_recurring_creation(rec_id, [], result, True)
                if not result:
                    return "Subevent not found with identifier '{}'".format(rec_id), 404
                return result
            if not result:
                return "Event not found with identifier '{}'".format(event_id), 404
            return mongo_to_dict(result)

        else:  # search database based on parameters
            query_dict = get_to_event_search(request)
            query = event_query(query_dict)
            results = db.Event.objects(__raw__ = query) #{'start': new Date('2017-06-14')})
            logging.debug('found {} events for query'.format(len(results)))
            if not results:
                return []

            if 'start' in query_dict:
                start = query_dict['start']
            else:
                start = datetime(2017,6,1)
            if 'end' in query_dict:
                end = query_dict['end']
            else:
                end = datetime(2017, 9, 20)

            events_list = []
            for event in results:
                # checks for recurrent events
                if 'recurrence' in event:
                    logging.debug("recurrence end: {}".format(mongo_to_dict(event)))
                    # checks for events from a recurrence that's been edited
                    events_list = recurring_to_full(event, events_list, start, end)
                else:
                    #logging.debug("normal: {}".format(mongo_to_dict(event)))
                    events_list.append(mongo_to_dict(event))
            #logging.debug("events_list: {}".format(events_list))
            return events_list

    def post(self):
        """Create new event with parameters passed in through args or form"""
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))  # combines args and form
        try:
            new_event = db.Event(**received_data)
            if new_event.labels == []:
                new_event.labels = ['unlabeled']
            if 'recurrence' in new_event:
                new_event.recurrence_end = find_recurrence_end(new_event)
                logging.debug("made an end: {}".format(new_event.recurrence_end))
            new_event.save()
        except ValidationError as error:
            return {'error_type': 'validation',
                    'validation_errors': [str(err) for err in error.errors],
                    'error_message': error.message}, 400
        else:  # return success
            return mongo_to_dict(new_event), 201

    def put(self, event_id):
        """Modify individual event"""
        received_data = request_to_dict(request)
        logging.debug("Received PUT data: {}".format(received_data))
        try:
            result = db.Event.objects(id=event_id).first()
            if not result:
                cur_parent_event = db.Event.objects(__raw__ = {'sub_events._id' : objectid.ObjectId(event_id)}).first()
                if cur_parent_event:
                    result = update_sub_event(received_data, cur_parent_event, objectid.ObjectId(event_id))
                else:
                    abort(404)
            else:
                if 'sid' in received_data and received_data['sid'] is not None:
                    iso_to_dt = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)

                    if 'rec_id' in received_data and received_data['rec_id'] is not None:
                        received_data['rec_id'] = dateutil.parser.parse(str(received_data['rec_id']))
                        result = create_sub_event(received_data, result)
                else:
                    result.update(**received_data)
                    result.reload()


        except ValidationError as error:
                return {'error_type': 'validation',
                        'validation_errors': [str(err) for err in error.errors],
                        'error_message': error.message}, 400
        else:  # return success
            return mongo_to_dict(result)

    def delete(self, event_id, rec_id=None):
        """Delete individual event"""
        logging.debug('Event requested: ' + event_id)
        result = db.Event.objects(id=event_id).first()
        if not result:
            cur_parent_event = db.Event.objects(__raw__ = {'sub_events._id' : objectid.ObjectId(event_id)}).first()
            if cur_parent_event:
                received_data = {'deleted': True}
                result = update_sub_event(received_data, cur_parent_event, objectid.ObjectId(event_id))
                logging.debug("Edited sub_event deleted")
        elif rec_id:
            sub_event_dummy = placeholder_recurring_creation(rec_id, [], result, True)
            sub_event_dummy['deleted'] = True
            create_sub_event(sub_event_dummy, result)
            logging.debug("Deleted sub_event for the first time")
        else:
            received_data = request_to_dict(request)
            logging.debug("Received DELETE data: {}".format(received_data))
            result.delete()
            return mongo_to_dict(result)
