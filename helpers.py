#!/usr/bin/env python3
"""Miscellaneous helper functions of varying usefulness
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
import logging
import pdb

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY, HOURLY, MINUTELY
from datetime import datetime, timedelta
from bson import objectid

import isodate

import database as db


def mongo_to_dict(obj):
    """Get dictionary from mongoengine object
    id is represented as a string
    """

    obj_dict = dict(obj.to_mongo())
    obj_dict['id'] = str(obj_dict['_id'])
    del(obj_dict['_id'])

    return obj_dict


def request_to_dict(request):
    """Convert incoming flask requests for objects into a dict"""
    req_dict = request.values.to_dict(flat=True)
    if request.is_json:
        req_dict = request.get_json()  # get_dict returns python dictionary object
    obj_dict = {k: v for k, v in req_dict.items() if v != ""}

    return obj_dict
     

def create_ics_event(event,recurrence=False):
    new_event = Event()
    new_event.add('summary', event['title'])
    new_event.add('location', event['location'])
    new_event.add('description', event['description'])
    new_event.add('dtstart', event['start'])
    if event['end'] is not None:
        new_event.add('dtend', event['end'])
    new_event.add('TRANSP', 'OPAQUE')

    if recurrence==False:
        uid = str(event['id'])
    else:
        uid = str(event['sid'])
        new_event.add('RECURRENCE-ID', event['rec_id'])
    new_event.add('UID', uid)
    return(new_event)

def create_ics_recurrence(new_event, recurrence):
    rec_ics_string = {}
    frequency = recurrence['frequency']
    interval = recurrence['interval']
    rec_ics_string['freq'] = frequency
    rec_ics_string['interval'] = interval

    if 'until' in recurrence:
        rec_ics_string['until'] = reccurrence['until']
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
    #initialize calendar object
    cal = Calendar()
    for event in events:
        new_event = create_ics_event(event)

        recurrence = event['recurrence']
        if recurrence:
            new_event = create_ics_recurrence(new_event, recurrence)

        if event['sub_events']:
            for sub_event in event['sub_events']:
                new_sub_event = create_ics_event(sub_event, True)
                cal.add_component(new_sub_event)
                new_event.add('EXDATE', sub_event['rec_id'])

        #vevent.add('attendee', 'MAILTO:emily.lepert@gmail.com')

        cal.add_component(new_event)


    response = cal.to_ical()
    return response

def ics_to_mongo(component):
    event_def = {}
    '''
    event_def['title']
    event_def['description']
    event_def['url']
    event_def['email']
    event_def['start']
    event_def['end']
    event_def['end_recurrence']
    event_def['']
    '''


def get_to_event_search(request):
    """Build search dictionary based on get parameters"""
    req_dict = request_to_dict(request)
    visibilities = {
        'public': ['public'],
        'olin': ['public', 'olin'],
        'students': ['public', 'olin', 'students'],
    }
    split_into_list = lambda a: a if isinstance(a, list) else a.split(',')
    preprocessing = {
        'labels': split_into_list,  # split labels on commas if not already list
        'labels_and': split_into_list,
        'labels_not': split_into_list,
        'visibility': lambda a: visibilities.get(a, None),  # search based on list
    }

    search_dict = req_dict
    for key, process in preprocessing.items():
        if key in search_dict.keys():
            search_dict[key] = process(search_dict[key])
    return search_dict


def event_query(search_dict):
    """Build mongo query for searching events based on query
    By default FullCalendar sends 'start' and 'end' as ISO8601 date strings"""
    params = {
        'start': lambda a: {'start__gte': a},
        'end': lambda a: {'end__lte': a},
        'labels': lambda a: {'labels__in': a},
        'labels_and': lambda a: {'labels__all': a},
        'labels_not': lambda a: {'labels__nin': a},
        'visibility': lambda a: {'visibility__in': a},
    }

    query = {}
    for key, get_pattern in params.items():
        if key in search_dict.keys():
            query.update(get_pattern(search_dict[key]))
    logging.debug('new query: {}'.format(query))
    return query


def recurring_to_full(event, events_list, start, end):
    if 'sub_events' in event:
        for sub_event in event['sub_events']:
            if sub_event['start'] <= end and sub_event['start'] >= start:
                events_list.append(sub_event)

    rec_type_list = ['YEARLY', 'MONTHLY', 'WEEKLY', 'DAILY']
    
    recurrence = event.recurrence
    
    rFrequency = rec_type_list.index(recurrence['frequency'])
    rInterval = recurrence['interval']
    rCount = recurrence['count'] if 'count' in recurrence else None
    rUntil = recurrence['until'] if 'until' in recurrence else None
    rByMonth = recurrence['BYMONTH'] if 'BYMONTH' in recurrence else None
    rByMonthDay = recurrence['BYMONTHDAY'] if 'BYMONTHDAY' in recurrence else None
    rByDay = recurrence['BYDAY'] if 'BYDAY' in recurrence else None


    rule_list = list(rrule(freq=rFrequency, count=int(rCount), interval=int(rInterval), until=rUntil, bymonth=rByMonth, \
        bymonthday=rByMonthDay, byweekday=None, dtstart=event['start']))

    for instance in rule_list:
        if instance >= start and instance < end:
            events_list = placeholder_recurring_creation(instance, events_list, event)

    return(events_list)

def placeholder_recurring_creation(instance, events_list, event):
    instance = datetime.strptime(str(instance), "%Y-%m-%d %H:%M:%S")
    event_end = datetime.strptime(str(event['end']), "%Y-%m-%d %H:%M:%S")
    event_start = datetime.strptime(str(event['start']), "%Y-%m-%d %H:%M:%S")

    repeat = False
    if 'sub_events' in event:
        for individual in event['sub_events']:
            indiv = datetime.strptime(str(individual['rec_id']), "%Y-%m-%d %H:%M:%S")
            if instance == indiv:
                repeat = True

    if repeat == False:
        fake_object = {}
        fake_object['title'] = event['title']
        fake_object['location'] = event['location']
        fake_object['description'] = event['description']
        fake_object['start'] = isodate.parse_datetime(instance.isoformat())
        fake_object['end'] = isodate.parse_datetime((event_end-event_start+instance).isoformat())  #.isoformat()
        fake_object['id'] = event['id']
        events_list.append(fake_object) #json.dumps(fake_object, default=json_util.default))

    return(events_list)


def update_sub_event(received_data):
    if 'rec_id' in received_data:
        rec_event = db.RecurringEventExc(**received_data)

        record_id = db.Event.objects(__raw__={'_id': objectid.ObjectId(received_data['sid'])})

        cur_sub_event = db.Event.objects(__raw__ = { '$and' : [
            {'_id': objectid.ObjectId(received_data['sid'])},
            {'sub_events.rec_id' : received_data['rec_id']}]})

        if cur_sub_event:
            cur_sub_event.update(set__sub_events__S=rec_event)
        else:
            record_id.update(add_to_set__sub_events=rec_event)

        logging.debug("Updated reccurence with event with id {}".format(record_id))
    else:
        #record_id = db.Event.objects(id=event['id']).update(inc__id__S=event)  # Update record
        logging.debug("Updated entry with id {}".format(record_id))

    return(record_id)


