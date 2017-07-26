#!/usr/bin/env python3
"""Type converting helper functions
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
from mongoengine import ValidationError

import logging
import pdb
import pytz

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from datetime import datetime, timedelta, timezone, date
from bson import objectid
from mongoengine import *
from icalendar import Calendar

import isodate
import dateutil.parser
import requests

from abe import database as db


def mongo_to_dict(obj):
    """Get dictionary from mongoengine object
    id is represented as a string

    obj         A mongodb object that will be converted to a dictionary
    """
    return_data = []
    if obj is None:
        return None

    # converts the mongoDB id for documents to a string from an ObjectID object
    if isinstance(obj, Document):
        return_data.append(("id",str(obj.id)))

    for field_name in obj._fields:

        if field_name in obj:  # check if field is populated
            if field_name in ("id",):
                continue

            data = obj[field_name]
            if isinstance(obj._fields[field_name], ListField):
                return_data.append((field_name, list_field_to_dict(data)))
            elif isinstance(obj._fields[field_name], EmbeddedDocumentField):
                return_data.append((field_name, mongo_to_dict(data)))
            elif isinstance(obj._fields[field_name], DictField):
                return_data.append((field_name, data))
            else:
                return_data.append((field_name, mongo_to_python_type(obj._fields[field_name], data)))

    return dict(return_data)


def list_field_to_dict(list_field):
    """
    Converts a list of mongodb Objects to a dictionary object

    list_field          list of embedded documents or other object types
    """

    return_data = []

    for item in list_field:
        # if list is of embedded documents, convert each document to a dictionary
        if isinstance(item, EmbeddedDocument):
            return_data.append(mongo_to_dict(item))
        # convert the data type
        else:
            return_data.append(mongo_to_python_type(item,item))

    return return_data


def mongo_to_python_type(field, data):
    """
    Converts certain fields to appropriate data types

    field       A field in a mongoDB object

    data        corresponding data to the field
    """
    if isinstance(field, ObjectIdField):
        return str(data)
    elif isinstance(field, DecimalField):
        return data
    elif isinstance(field, BooleanField):
        return data
    else:
        return str(data)


def request_to_dict(request):
    """Convert incoming flask requests for objects into a dict"""

    req_dict = request.values.to_dict(flat=True)
    if request.is_json:
        req_dict = request.get_json()  # get_dict returns python dictionary object
    obj_dict = {k: v for k, v in req_dict.items() if v != ""}
    return obj_dict
