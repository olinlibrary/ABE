#!/usr/bin/env python3
"""ICS Resource models for flask"""

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
from abe.helper_functions.converting_helpers import request_to_dict
from abe.helper_functions.query_helpers import get_to_event_search, event_query
from abe.helper_functions.ics_helpers import mongo_to_ics, extract_ics

class ICSApi(Resource):
    """API for interacting with ics feeds"""

    def get(self):
        """
        Returns an ICS feed when requested
        """
        # configure ics specs from fullcalendar to be mongoengine searchable
        query = event_query(get_to_event_search(request))
        results = db.Event.objects(__raw__=query)
        # converts mongoDB objects to an ICS format
        response = mongo_to_ics(results)
        logging.debug("ics feed created")
        cd = "attachment;filename=abe.ics"
        return Response(response,
                   mimetype="text/calendar",
                   headers={"Content-Disposition": cd})


    def post(self):
        """
        Converts an ICS feed input to mongoDB objects
        """
        try:
            #reads outside ics feed
            url = request_to_dict(request)
            data = requests.get(url['url'].strip()).content.decode('utf-8')
            cal = Calendar.from_ical(data)
            if 'labels' in url:
                labels = url['labels']
            else:
                labels = ['unlabeled']

            extract_ics(cal, url['url'], labels)
        except ValidationError as error:
            return {'error_type': 'validation',
                    'validation_errors': [str(err) for err in error.errors],
                    'error_message': error.message}, 400
        
