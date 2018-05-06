#!/usr/bin/env python3
"""Event Resource models for flask"""

import logging
from datetime import timedelta

import dateutil.parser
from bson import objectid
from flask import abort, request
from flask_restplus import Namespace, Resource, fields

from abe import database as db
from abe.auth import edit_auth_required
from abe.helper_functions.converting_helpers import mongo_to_dict, request_to_dict
from abe.helper_functions.mongodb_helpers import mongo_resource_errors
from abe.helper_functions.query_helpers import event_query, get_to_event_search
from abe.helper_functions.recurring_helpers import placeholder_recurring_creation, recurring_to_full
from abe.helper_functions.sub_event_helpers import (access_sub_event, create_sub_event, find_recurrence_end,
                                                    sub_event_to_full, update_sub_event)

api = Namespace('events', description='Events related operations')

# This should be kept in sync with the document model, which drives the format
event_model = api.model('Events_Model', {
    'title': fields.String(example="Tea time"),
    'start': fields.DateTime(dt_format='iso8601'),
    'end': fields.DateTime(dt_format='iso8601'),
    'location': fields.String(example="EH4L"),
    'description': fields.String(example="Time for tea"),
    'visibility': fields.String(enum=['public', 'olin', 'students']),
    'labels': fields.List(fields.String, description="One of the labels in the DB"),
    'allDay': fields.Boolean
})


class EventApi(Resource):
    """API for interacting with events"""

    @mongo_resource_errors
    def get(self, event_id=None, rec_id=None):
        """
        Retrieve events from mongoDB

        event_id        the id of the mongoDB event requested to be found

        rec_id          the rec_id of the sub_event information requested to be retrieved
        """

        if event_id:  # use event id if present
            logging.debug('Event requested: ' + event_id)
            result = db.Event.objects(id=event_id).first()

            if not result:  # if there are no events with the event_id given
                # search for sub_events with that id and save the parent event
                cur_parent_event = db.Event.objects(__raw__={'sub_events._id': objectid.ObjectId(event_id)}).first()

                if cur_parent_event:  # if a sub_event was found
                    # access the information of the sub_event
                    cur_sub_event = access_sub_event(mongo_to_dict(cur_parent_event), objectid.ObjectId(event_id))
                    # expand the sub_event to inherit from the parent event
                    return sub_event_to_full(cur_sub_event, cur_parent_event)
                else:
                    logging.debug("No sub_event found")
                    abort(404)
            # if an event was found and there is a rec_id given, a sub_event needs to be returned
            elif rec_id:
                # the json response will be used to display the information of the sub_event before it is edited
                logging.debug('Sub_event requested: ' + rec_id)
                # return a json response with the parent event information filled in with
                # the start and end datetimes updated from the rec_id
                result = placeholder_recurring_creation(rec_id, [], result, True)
                if not result:
                    return "Subevent not found with identifier '{}'".format(rec_id), 404
                return result

            if not result:
                return "Event not found with identifier '{}'".format(event_id), 404
            return mongo_to_dict(result)

        else:  # search database based on parameters
            # make a query to the database
            query_dict = get_to_event_search(request)

            query_time_period = query_dict['end'] - query_dict['start']
            if query_time_period > timedelta(days=366):
                return "Too wide of date range in query. Max date range of 1 year allowed.", 404

            query = event_query(query_dict)
            results = db.Event.objects(__raw__=query)  # {'start': new Date('2017-06-14')})
            logging.debug('found {} events for query'.format(len(results)))

            if not results:  # if no results were found
                return []

            # date range for query
            start = query_dict['start']
            end = query_dict['end']

            events_list = []
            for event in results:

                if 'recurrence' in event:  # checks for recurrent events
                    # expands a recurring event defintion into a json response with individual events
                    events_list = recurring_to_full(event, events_list, start, end)
                else:  # appends the event information as a dictionary
                    events_list.append(mongo_to_dict(event))
            return events_list

    @edit_auth_required
    @mongo_resource_errors
    @api.expect(event_model)
    def post(self):
        """
        Create new event with parameters passed in through args or form
        """
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))  # combines args and form
        new_event = db.Event(**received_data)
        if new_event.labels == []:  # if no labels were given
            new_event.labels = ['unlabeled']
        if 'recurrence' in new_event:  # if this is a recurring event
            if not new_event.recurrence.forever:  # if it doesn't recurr forever
                # find the end of the recurrence
                new_event.recurrence_end = find_recurrence_end(new_event)
        new_event.save()
        return mongo_to_dict(new_event), 201

    @edit_auth_required
    @mongo_resource_errors
    @api.expect(event_model)
    def put(self, event_id):
        """
        Modify individual event

        event_id        id of the event to modify
        """
        received_data = request_to_dict(request)
        logging.debug("Received PUT data: {}".format(received_data))
        result = db.Event.objects(id=event_id).first()
        if not result:  # if no event was found
            # try finding a sub_event with the id and save the parent event it is stored under
            cur_parent_event = db.Event.objects(__raw__={'sub_events._id': objectid.ObjectId(event_id)}).first()
            if cur_parent_event:  # if a sub_event was found, updated it with the received_data
                result = update_sub_event(received_data, cur_parent_event, objectid.ObjectId(event_id))
            else:
                abort(404)
        else:  # if event was found
            # if the received data is a new sub_event
            if 'sid' in received_data and received_data['sid'] is not None:

                # create a new sub_event document
                if 'rec_id' in received_data and received_data['rec_id'] is not None:
                    received_data['rec_id'] = dateutil.parser.parse(str(received_data['rec_id']))
                    result = create_sub_event(received_data, result)
            else:  # if this a normal event to be updated
                result.update(**received_data)
                result.reload()
        return mongo_to_dict(result)

    @edit_auth_required
    @mongo_resource_errors
    def delete(self, event_id, rec_id=None):
        """
        Delete individual event

        event_id        the id of the event to be deleted

        rec_id          the rec_id of a sub_event to be deleted
        """
        logging.debug('Event requested: ' + event_id)
        result = db.Event.objects(id=event_id).first()
        if not result:  # if no event is found with the id given
            # try finding a sub_event with that id
            cur_parent_event = db.Event.objects(__raw__={'sub_events._id': objectid.ObjectId(event_id)}).first()
            if cur_parent_event:  # if found update the deleted field of the sub_event
                received_data = {'deleted': True}
                result = update_sub_event(received_data, cur_parent_event, objectid.ObjectId(event_id))
                logging.debug("Edited sub_event deleted")
        elif rec_id:  # if this is a sub_event of a recurring event that has not been created yet
            sub_event_dummy = placeholder_recurring_creation(rec_id, [], result, True)
            sub_event_dummy['deleted'] = True
            # create a sub_event with the deleted field set to true
            create_sub_event(sub_event_dummy, result)
            logging.debug("Deleted sub_event for the first time")
        else:  # if a normal event is to be deleted
            received_data = request_to_dict(request)
            logging.debug("Received DELETE data: {}".format(received_data))
            result.delete()
            return mongo_to_dict(result)


api.add_resource(EventApi, '/', methods=['GET', 'POST'], endpoint='event')
# TODO: add route for string/gphycat links
api.add_resource(EventApi, '/<string:event_id>',
                 methods=['GET', 'PUT', 'PATCH', 'DELETE'],
                 endpoint='event_id')
api.add_resource(EventApi, '/<string:event_id>/<string:rec_id>',
                 methods=['GET', 'PUT', 'PATCH', 'DELETE'],
                 endpoint='rec_id')  # TODO: add route for string/gphycat links
