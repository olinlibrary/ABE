#!/usr/bin/env python3
"""Sub event helper functions
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

def duplicate_query_check(sub_event_dict, parent_event):
    """checks whether a dictionary has the same field-value pair as a parent event
    used to check for duplicate information in sub_events and their parent events
    """
    parent_event_dict = mongo_to_dict(parent_event)
    fields_to_pop = []
    for field in sub_event_dict:
        if field in parent_event_dict:
            if sub_event_dict[field] == parent_event_dict[field]:
               fields_to_pop.append(field)
    for field in fields_to_pop:
        sub_event_dict.pop(field)

    return(sub_event_dict)

def create_sub_event(received_data, parent_event):
    """creates an edited event in a recurring series for the first time
    """
    sub_event_dict = duplicate_query_check(received_data, parent_event)
    rec_event = db.RecurringEventExc(**sub_event_dict)
    parent_event.update(add_to_set__sub_events=rec_event)
    parent_event.reload()

    return(rec_event)

def update_sub_event(received_data, parent_event, sub_event_id, ics=False):
    """edits a sub_event that has already been created
    """
    for sub_event in parent_event.sub_events:
        if ics == False:
            if sub_event['_id']== sub_event_id:
                updated_sub_event_dict = create_new_sub_event_defintion(mongo_to_dict(sub_event), received_data, parent_event)
                updated_sub_event = db.RecurringEventExc(**updated_sub_event_dict)
                parent_event.update(pull__sub_events___id=sub_event_id)
                parent_event.update(add_to_set__sub_events=updated_sub_event_dict)
                parent_event.recurrence_end = find_recurrence_end(parent_event)
                parent_event.save()
                parent_event.reload()
                return(updated_sub_event)
        elif ics == True:
            sub_event_compare = sub_event["rec_id"].replace(tzinfo=pytz.UTC)
            if sub_event_compare == sub_event_id:
                updated_sub_event_dict = create_new_sub_event_defintion(mongo_to_dict(sub_event), received_data, parent_event)
                updated_sub_event = db.RecurringEventExc(**updated_sub_event_dict)
                parent_event.update(pull__sub_events__rec_id=sub_event_id)
                parent_event.update(add_to_set__sub_events=updated_sub_event_dict)
                parent_event.recurrence_end = find_recurrence_end(parent_event)
                parent_event.save()
                parent_event.reload()
                return(updated_sub_event)

def sub_event_to_full(sub_event_dict, event):
    """expands a sub_event definition to have all fields full_Calendar requires
    uses its parent definition to fill in the blanks
    """
    recurring_def_fields = ["end_recurrence", "recurrence", "sub_events"]
    for field in event:
        if field not in sub_event_dict:
            if field not in recurring_def_fields:
                if field == 'id':
                    sub_event_dict["sid"] = str(event[field])
                elif field == 'ics_id':
                    sub_event_dict[field] = str(event[field])
                else:
                    sub_event_dict[field] = event[field]
    sub_event_dict["id"] = sub_event_dict.pop("_id")
    sub_event_dict['start'] = dateutil.parser.parse(str(sub_event_dict['start']))
    if 'end' in sub_event_dict:
        sub_event_dict['end'] = dateutil.parser.parse(str(sub_event_dict['end']))
    if 'rec_id' in sub_event_dict:
        sub_event_dict['rec_id'] = dateutil.parser.parse(str(sub_event_dict['rec_id']))
    return(sub_event_dict)

def access_sub_event(parent_event, sub_event_id):
    """gets the sub_event from a parent_event and returns it
    """
    for sub_event in parent_event['sub_events']:
        if sub_event['_id'] == str(sub_event_id):
            return(sub_event)

def create_new_sub_event_defintion(sub_event, updates, parent_event):
    """based on the old sub_event definition and updates submitted
    generates a new sub_event definition
    """
    sub_event.update(updates)
    sub_event = duplicate_query_check(sub_event, parent_event)
    return(sub_event)


def instance_creation(event):
    rec_type_list = ['YEARLY', 'MONTHLY', 'WEEKLY', 'DAILY']

    day_list = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

    recurrence = event.recurrence
    ensure_date_time = lambda a: dateutil.parser.parse(a) if not isinstance(a, datetime) else a

    rFrequency = rec_type_list.index(recurrence['frequency'])
    rInterval = int(recurrence['interval'])
    rCount = int(recurrence['count']) if 'count' in recurrence else None
    rUntil = ensure_date_time(recurrence['until']) if 'until' in recurrence else None
    rByMonth = recurrence['by_month'] if 'by_month' in recurrence else None
    rByMonthDay = recurrence['by_month_day'] if 'by_month_day' in recurrence else None

    if 'by_day' in recurrence:
        rByDay = []
        for i in recurrence['by_day']:
            rByDay.append(day_list.index(i))
    else:
        rByDay = None

    rule_list = list(rrule(freq=rFrequency, count=rCount, interval=rInterval, until=rUntil, bymonth=rByMonth, \
        bymonthday=rByMonthDay, byweekday=rByDay, dtstart=ensure_date_time(event['start'])))

    return(rule_list)


def find_recurrence_end(event):
    rule_list = instance_creation(event)
    return(rule_list[-1])