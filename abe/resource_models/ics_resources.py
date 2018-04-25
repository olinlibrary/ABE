#!/usr/bin/env python3
"""ICS Resource models for flask"""

from flask import jsonify, request, abort, Response, make_response
from flask_restplus import Resource, fields
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
from abe.app import api
from abe.helper_functions.converting_helpers import request_to_dict
from abe.helper_functions.query_helpers import get_to_event_search, event_query
from abe.helper_functions.ics_helpers import mongo_to_ics, extract_ics

ics_model = api.model("ICS_Model", {
    "url" : fields.Url(required=True),
    "labels" : fields.List(fields.String, required=True)
})

class ICSApi(Resource):
    """API for interacting with ics feeds"""

    @api.deprecated
    def get(self):
        """
        Deprecated, use SubscriptionICSFeed get instead.
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

    @api.expect(ics_model)
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
