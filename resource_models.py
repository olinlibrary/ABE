#!/usr/bin/env python3
"""Resource models for flask"""
from flask import jsonify, request, abort, make_response
from flask_restful import Resource
from mongoengine import ValidationError
from bson.objectid import ObjectId

from pprint import pprint, pformat
import pdb

from helpers import *

import logging

import database as db


class EventApi(Resource):
    """API for interacting with events"""

    def get(self, event_id=None):
        """Retrieve events"""
        if event_id:  # use event id if present
            logging.debug('Event requested: ' + event_id)
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

            # TODO: expand recurrences
            return jsonify([mongo_to_dict(result) for result in results])  # TODO: improve datetime output

    def post(self):
        """Create new event with parameters passed in through args or form"""
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))
        try:
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
        """Modify individual event"""
        logging.debug('Event requested: ' + event_id)
        result = db.Event.objects(id=event_id).first()
        if not result:
            abort(404)

        received_data = request_to_dict(request)
        logging.debug("Received PUT data: {}".format(received_data))
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
