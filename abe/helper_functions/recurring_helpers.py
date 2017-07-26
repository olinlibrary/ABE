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
from datetime import datetime, timedelta, timezone, date
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
    event           mongoDB event

    events_list     list of events to be returned

    start, end      start and end indicating the query date range
    """

    if 'sub_events' in event: # if there are sub_events in event
        for sub_event in event['sub_events']:
            if 'start' in sub_event:
                # if the sub_event fits into the date range and is not deleted
                if sub_event['start'] <= end and sub_event['start'] >= start \
                    and sub_event['deleted']==False: 
                    events_list.append(sub_event_to_full(mongo_to_dict(sub_event), event))

    # generate a list of all datetimes a recurring event would occur 
    rule_list = instance_creation(event, end)

    # for each instance create a full event definition based on its parent event
    for instance in rule_list:
        convert_timezone = lambda a: a.replace(tzinfo=pytz.UTC) if isinstance(a, datetime) else a
        if convert_timezone(instance) >= convert_timezone(start) and convert_timezone(instance) < convert_timezone(end):
            events_list = placeholder_recurring_creation(instance, events_list, event)

    return(events_list)


def placeholder_recurring_creation(instance, events_list, event, edit_recurrence=False):
    """appends a dummy dictionary to a list if it's to display on the calendar
    returns a single dummy dicitionary before editing of a single reucrring event

    edit_recurrence         If true, this function will return a singular fake_object
                            so that fullcalendar can display the information for someone
                            who wants to edit a sub_event for the first time
    """
    instance = dateutil.parser.parse(str(instance))
    event_end = dateutil.parser.parse(str(event['end']))
    event_start = dateutil.parser.parse(str(event['start']))

    fields = ['title', 'location', 'description', 'labels']

    repeat = False
    if 'sub_events' in event:
        for individual in event['sub_events']:
            indiv = dateutil.parser.parse(str(individual['rec_id']))
            # checks to see if the instance actually occurs at the time a sub_event 
            # would have occurred
            if instance == indiv: 
                repeat = True

    if repeat == False: # if the instance is not a repeat of a sub_event
        fake_object = {}
        fake_object['start'] = isodate.parse_datetime(instance.isoformat())
        fake_object['end'] = isodate.parse_datetime((event_end-event_start+instance).isoformat())
        fake_object['sid'] = str(event['id'])

        for field in fields:
            if field in event:
                fake_object[field] = event[field]

        events_list.append(fake_object)

        if edit_recurrence == True: # return only the fake_object
            fake_object['rec_id'] = isodate.parse_datetime(instance.isoformat())
            return(fake_object)
    return(events_list)



