#!/usr/bin/env python3
"""Miscellaneous helper functions of varying usefulness
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
from mongoengine import ValidationError

import logging
import pdb

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY
from datetime import datetime, timedelta
from bson import objectid
from mongoengine import *

import isodate
import dateutil.parser

from . import database as db


def mongo_to_dict(obj):
    """Get dictionary from mongoengine object
    id is represented as a string
    """
    return_data = []
    if obj is None:
        return None

    if isinstance(obj, Document):
        return_data.append(("id",str(obj.id)))

    for field_name in obj._fields:

        if obj[field_name]:  # check if field is populated
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
                return_data.append((field_name, mongo_to_python_type(obj._fields[field_name],data)))

    return dict(return_data)


def list_field_to_dict(list_field):

    return_data = []

    for item in list_field:
        if isinstance(item, EmbeddedDocument):
            return_data.append(mongo_to_dict(item))
        else:
            return_data.append(mongo_to_python_type(item,item))


    return return_data


def mongo_to_python_type(field,data):
    if isinstance(field, ObjectIdField):
        return str(data)
    elif isinstance(field, DecimalField):
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


def create_ics_event(event,recurrence=False):
    """creates ICS event definition
    """
    new_event = Event()
    new_event.add('summary', event['title'])
    new_event.add('location', event['location'])
    new_event.add('description', event['description'])
    new_event.add('dtstart', event['start'])
    if 'end' in event:
        new_event.add('dtend', event['end'])
    new_event.add('TRANSP', 'OPAQUE')

    if recurrence == False:
        uid = str(event['id'])
    else:
        uid = str(event['sid'])
        new_event.add('RECURRENCE-ID', event['rec_id'])

    new_event.add('UID', uid)
    return(new_event)


def create_ics_recurrence(new_event, recurrence):
    """creates the ICS rrule definition
    """
    rec_ics_string = {}
    frequency = recurrence['frequency']
    interval = recurrence['interval']
    rec_ics_string['freq'] = frequency
    rec_ics_string['interval'] = interval

    if 'until' in recurrence:
        rec_ics_string['until'] = recurrence['until']
    elif 'count' in recurrence:
        rec_ics_string['count'] = recurrence['count']

    if frequency == 'WEEKLY':
        rec_ics_string['byday'] = recurrence['by_day']

    elif frequency == 'MONTHLY':
        if recurrence['by_day']:
            rec_ics_string['byday'] = recurrence['by_day']
        elif recurrence['by_month_day']:
            rec_ics_string['bymonthday'] = recurrence['by_month_day']

    new_event.add('RRULE', rec_ics_string)
    return(new_event)


def mongo_to_ics(events):
    """creates the iCal based on the MongoDb database
    and events submitted
    """

    #initialize calendar object
    cal = Calendar()
    for event in events:
        new_event = create_ics_event(event)

        recurrence = event['recurrence']
        if recurrence:
            new_event = create_ics_recurrence(new_event, recurrence)

        if event['sub_events']:
            for sub_event in event['sub_events']:
                full_sub_event = sub_event_to_full(mongo_to_dict(sub_event), event)
                new_sub_event = create_ics_event(full_sub_event, True)
                cal.add_component(new_sub_event)
                new_event.add('EXDATE', sub_event['rec_id'])

        #vevent.add('attendee', 'MAILTO:emily.lepert@gmail.com')

        cal.add_component(new_event)


    response = cal.to_ical()
    return response


def ics_to_mongo(component, labels):
    event_def = {}
    event_def['title'] = str(component.get('summary'))
    event_def['description'] = str(component.get('description'))
    event_def['location'] = str(component.get('location'))
    event_def['start'] = component.get('dtstart').dt
    event_def['end'] = component.get('dtend').dt
    event_def['labels'] = labels
    if component.get('rrule'):
        rrule = component.get('rrule')
        rec_def = {}
        rec_def['frequency'] = str(rrule.get('freq')[0])
        if 'until' in rrule:
            rec_def['until'] = rrule.get('until')[0]
        if 'BYDAY' in rrule:
            rec_def['by_day'] = rrule.get('BYDAY')
        if 'INTERVAL' in rrule:
            rec_def['interval'] = str(rrule.get('INTERVAL')[0])
        else:
            rec_def['interval'] = '1'
        #rec_def['interval'] = '1' if 'INTERVAL' not in rrule else str(component.get('interval'))
        event_def['recurrence'] = rec_def

    db.Event(**event_def).save()


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

    query_reg_event = {}
    for key, get_pattern in params_reg_event.items():
        if key in search_dict.keys():
            query_reg_event.update(get_pattern(search_dict[key]))

    query_rec_event = {}
    for key, get_pattern in params_recu_event.items():
        if key in search_dict.keys():
            query_rec_event.update(get_pattern(search_dict[key]))

    query = {'$or': [query_reg_event,query_rec_event]}
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
    logging.debug("sub_event_dict {}".format(sub_event_dict))
    rec_event = db.RecurringEventExc(**sub_event_dict)
    parent_event.update(add_to_set__sub_events=rec_event)
    parent_event.reload()

    return(rec_event)

def update_sub_event(received_data, parent_event, sub_event_id):
    """edits a sub_event that has already been created
    """
    for sub_event in parent_event.sub_events:
        if sub_event["_id"] == sub_event_id:
            updated_sub_event_dict = create_new_sub_event_defintion(mongo_to_dict(sub_event), received_data, parent_event)
            updated_sub_event = db.RecurringEventExc(**updated_sub_event_dict)
            parent_event.update(pull__sub_events___id=sub_event_id)
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
    """based on the hold sub_event definition and updates submitted
    generates a new sub_event definition
    """
    sub_event.update(updates)
    sub_event = duplicate_query_check(sub_event, parent_event)
    return(sub_event)

def find_recurrence_end(event):
    rule_list = instance_creation(event)
    return(rule_list[-1])

def printing_a_message():
    return("return a message")

