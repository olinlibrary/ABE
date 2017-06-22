#!/usr/bin/env python3
"""Resource models for flask"""
from flask import jsonify, request, abort
from flask_restful import Resource
from mongoengine import ValidationError

from pprint import pprint, pformat
import pdb

from helpers import mongo_to_dict, request_to_dict

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
            # TODO: search based on parameters
            results = db.Event.objects()
            if not results:
                abort(404)

            # TODO: expand recurrences
            return jsonify([mongo_to_dict(result) for result in results])  # TODO: improve datetime output

    def post(self):
        """Create new event with parameters passed in through args or form"""
        # pdb.set_trace()
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))
        try:
            new_event = db.Event(**received_data)
            # pdb.set_trace()
            new_event.save()
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
