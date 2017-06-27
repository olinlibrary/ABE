#!/usr/bin/env python3
"""Miscellaneous helper functions of varying usefulness
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
import logging
import pdb
from icalendar import Calendar, Event, vCalAddress, vText, vDatetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, YEARLY, HOURLY, MINUTELY


def mongo_to_dict(obj):
    """Get dictionary from mongoengine object
    id is represented as a string
    """

    obj_dict = dict(obj.to_mongo())
    obj_dict['id'] = str(obj_dict['_id'])
    del(obj_dict['_id'])

    return obj_dict


def request_to_dict(request):
    """Convert incoming flask requests into a dict"""
    req_dict = request.values.to_dict()
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

def create_ics(events):
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
