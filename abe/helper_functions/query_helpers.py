#!/usr/bin/env python3
"""Querying helper functions
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
from mongoengine import ValidationError

import logging
import pdb
import pytz

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from datetime import datetime, timedelta, timezone, date
from dateutil.relativedelta import relativedelta
from bson import objectid
from mongoengine import *
from icalendar import Calendar

import isodate
import dateutil.parser
import requests

from abe import database as db
from abe.helper_functions.converting_helpers import request_to_dict


def get_to_event_search(request):
    """Build search dictionary based on get parameters"""
    req_dict = request_to_dict(request)
    visibilities = {
        'public': ['public'],
        'olin': ['public', 'olin'],
        'students': ['public', 'olin', 'students'],
    }

    split_into_list = lambda a: a if isinstance(a, list) else a.split(',')
    ensure_date_time = lambda a: dateutil.parser.parse(a) if not isinstance(a, datetime) else a

    preprocessing = {
        'labels': split_into_list,  # split labels on commas if not already list
        'labels_and': split_into_list,
        'labels_not': split_into_list,
        'visibility': lambda a: visibilities.get(a, None),  # search based on list
        'start': ensure_date_time,
        'end': ensure_date_time,
    }

    search_dict = req_dict
    for key, process in preprocessing.items():
        if key in search_dict.keys():
            search_dict[key] = process(search_dict[key])

    # create a default date range if none is given
    now = datetime.now()
    if 'start' not in search_dict:
        search_dict['start'] = now + relativedelta(months=-1)
    if 'end' not in search_dict:
        search_dict['end'] = now + relativedelta(months=+2)

    return search_dict


def event_query(search_dict):
    """Build mongo query for searching events based on query
    By default FullCalendar sends 'start' and 'end' as ISO8601 date strings
    Has two queries: one for regular events and one for recurring events"""

    #the key in params dicts maps to the keys in the request given
    #the keys in the lambda functions map to the keys in MongoDb
    params_reg_event = {
        'start': lambda a: {'end' : {'$gte': a}},
        'end': lambda a: {'start' : {'$lte': a}},
        'labels': lambda a: {'labels' : {'$in': a}},
        'labels_and': lambda a: {'labels' : {'$all': a}},
        'labels_not': lambda a: {'labels' :{'$nin': a}},
        'visibility': lambda a: {'visibility' : {'$in': a}},
    }

    params_recu_event = {
        'start': lambda a: {'recurrence_end' : {'$gte': a}},
        'end': lambda a: {'start' : {'$lte': a}},
        'labels': lambda a: {'labels' : {'$in': a}},
        'labels_and': lambda a: {'labels' : {'$all': a}},
        'labels_not': lambda a: {'labels' :{'$nin': a}},
        'visibility': lambda a: {'visibility' : {'$in': a}},
    }

    # query for regular events
    query_reg_event = {}
    for key, get_pattern in params_reg_event.items():
        if key in search_dict.keys():
            query_reg_event.update(get_pattern(search_dict[key]))
    # query for recurring events with an end date
    query_rec_event = {}
    for key, get_pattern in params_recu_event.items():
        if key in search_dict.keys():
            query_rec_event.update(get_pattern(search_dict[key]))

    # query for recurring events with no end date
    query_forever = {'start' : {'$lte': search_dict['end']}, 'forever' : True}

    query = {'$or': [query_rec_event, query_reg_event, query_forever]}
    return query


def multi_search(table, thing_to_search, fields):
    """Search multiple fields with the same input
    This could be done with $or and __raw__ with mongoengine but ObjectID needs to be cast/checked correctly.
    """
    for field in fields:
        try:
            result = table.objects(**{field: thing_to_search}).first()
        except ValidationError:
            result = None
        if result:
            return result
    return None
