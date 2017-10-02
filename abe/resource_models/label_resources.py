#!/usr/bin/env python3
"""Label Resource models for flask"""

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
from abe.helper_functions.converting_helpers import mongo_to_dict, request_to_dict
from abe.helper_functions.query_helpers import multi_search


class LabelApi(Resource):
    """API for interacting with all labels (searching, creating)"""

    def get(self, label_name=None):
        """Retrieve labels"""
        if label_name:  # use label name/object id if present
            logging.debug('Label requested: ' + label_name)
            search_fields = ['name', 'id']
            result = multi_search(db.Label, label_name, search_fields)
            if not result:
                return "Label not found with identifier '{}'".format(label_name), 404
            else:
                return mongo_to_dict(result)
        else:  # search database based on parameters
            # TODO: search based on terms
            results = db.Label.objects()
            if not results:
                return []
            else:
                return [mongo_to_dict(result) for result in results]

    def post(self):
        """Create new label with parameters passed in through args or form"""
        received_data = request_to_dict(request)
        logging.debug("Received POST data: {}".format(received_data))
        try:
            new_label = db.Label(**received_data)
            new_label.save()
        except ValidationError as error:
            logging.warning("POST request rejected: {}".format(str(error)))
            return {'error_type': 'validation',
                    'validation_errors': [str(err) for err in error.errors],
                    'error_message': error.message}, 400
        else:  # return success
            return mongo_to_dict(new_label), 201

    def put(self, label_name):
        """Modify individual label"""
        received_data = request_to_dict(request)
        logging.debug("Received PUT data: {}".format(received_data))
        search_fields = ['name', 'id']
        result = multi_search(db.Label, label_name, search_fields)
        if not result:
            return "Label not found with identifier '{}'".format(label_name), 404

        try:
            result.update(**received_data)
        except ValidationError as error:
            return {'error_type': 'validation',
                    'validation_errors': [str(err) for err in error.errors],
                    'error_message': error.message}, 400

        else:  # return success
            return mongo_to_dict(result)

    def delete(self, label_name):
        """Delete individual label"""
        logging.debug('Label requested: ' + label_name)
        search_fields = ['name', 'id']
        result = multi_search(db.Label, label_name, search_fields)
        if not result:
            return "Label not found with identifier '{}'".format(label_name), 404

        received_data = request_to_dict(request)
        logging.debug("Received DELETE data: {}".format(received_data))
        result.delete()
        return mongo_to_dict(result)
