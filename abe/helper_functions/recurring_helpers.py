#!/usr/bin/env python3
"""Recurring event helper functions
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
from mongoengine import ValidationError

import logging
import pdb
import pytz

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from datetime import datetime, timedelta, timezone
from bson import objectid
from mongoengine import *
from icalendar import Calendar

import isodate
import dateutil.parser
import requests

from abe import database as db
from abe.helper_functions.converting_helpers import mongo_to_dict
from abe.helper_functions.sub_event_helpers import sub_event_to_full, instance_creation

def recurring_to_full(event, events_list, start, end):
    """Expands recurring events in MongoDb to multiple placeholder objects
    """
    if 'sub_events' in event:
        for sub_event in event['sub_events']:
            if 'start' in sub_event:
                if sub_event['start'] <= end and sub_event['start'] >= start \
                    and sub_event['deleted']==False:
                    events_list.append(sub_event_to_full(mongo_to_dict(sub_event), event))

    rule_list = instance_creation(event)

    for instance in rule_list:
        if instance >= start and instance < end:
            events_list = placeholder_recurring_creation(instance, events_list, event)

    return(events_list)


def placeholder_recurring_creation(instance, events_list, event, edit_recurrence=False):
    """appends a dummy dictionary to a list if it's to display on the calendar
    returns a single dummy dicitionary before editing of a single reucrring event
    """
    instance = dateutil.parser.parse(str(instance))
    event_end = dateutil.parser.parse(str(event['end']))
    event_start = dateutil.parser.parse(str(event['start']))

    repeat = False
    if 'sub_events' in event:
        for individual in event['sub_events']:
            indiv = dateutil.parser.parse(str(individual['rec_id']))
            if instance == indiv: # or (instance == indiv and individual['deleted']==True):
                repeat = True

    if repeat == False:
        fake_object = {}
        fake_object['title'] = event['title']
        fake_object['location'] = event['location']
        fake_object['description'] = event['description']
        fake_object['start'] = isodate.parse_datetime(instance.isoformat())
        fake_object['end'] = isodate.parse_datetime((event_end-event_start+instance).isoformat())  #.isoformat()
        fake_object['sid'] = str(event['id'])
        fake_object['labels'] = event['labels']

        events_list.append(fake_object) #json.dumps(fake_object, default=json_util.default))
        if edit_recurrence == True:
            fake_object['rec_id'] = isodate.parse_datetime(instance.isoformat())
            return(fake_object)
    return(events_list)



