#!/usr/bin/env python3
"""ICS helper functions
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
from mongoengine import ValidationError

import logging
import pdb
import pytz

from icalendar import Calendar, Event, vCalAddress, vText, vDatetime, Timezone
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
from abe.helper_functions.sub_event_helpers import create_sub_event, update_sub_event, sub_event_to_full, find_recurrence_end


def create_ics_event(event,recurrence=False):
    """
    This funciton creates a base ICS event definition. It uses the Event() class of the 
    iCalendar library.

    Supports the following arguments:
    event           A mongodb Event object

    recurrence      A boolean value indicating the event is part of a recurring event series.
                    If True then the UID of the ICS event will correspond to the sub_event id
                    (sid) of the event. A 'RECURRENCE-ID' field will be created with the event 
                    rec_id as its value.
                    If False then the UID of the ICS event will correspond to the event id (id)
                    of the event.
    """

    # helper function to truncate all day events to ignore times
    date_to_ics = lambda a: a[:-9].replace('-','')
    ensure_date_time = lambda a: dateutil.parser.parse(a) if not isinstance(a, datetime) else a

    # creates the Event
    new_event = Event()
    new_event.add('summary', event['title'])
    new_event.add('location', event['location'])
    new_event.add('description', event['description'])

    if event['allDay'] == True:
        start_string = 'dtstart;VALUE=DATE'
        end_string = 'dtend;VALUE=DATE'
        event_start = date_to_ics(ensure_date_time(event['start']).isoformat())
        event_end = date_to_ics(ensure_date_time(event['end']).isoformat())
        event_end = str(int(event_end) + 1)
    else:
        start_string = 'dtstart'
        end_string = 'dtend'
        
        utc = pytz.utc
        
        event_start = utc.localize(ensure_date_time(event['start']))
        event_end = utc.localize(ensure_date_time(event['end']))

    new_event.add(start_string, event_start)
    if 'end' in event:
        new_event.add(end_string, event_end)
    new_event.add('TRANSP', 'OPAQUE')

    if recurrence == False:
        uid = str(event['id'])
    else:
        uid = str(event['sid'])
        new_event.add('RECURRENCE-ID', ensure_date_time(event['rec_id']))

    new_event.add('UID', uid)
    return(new_event)


def create_ics_recurrence(new_event, recurrence):
    """
    creates the ICS rrule definition

    new_event           The current ics event that the recurrence 
                        definition will be added to

    recurrence          The recurrence defintion as stored in mongoDB
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

    elif frequency == 'YEARLY':
        if recurrence['by_month']:
            rec_ics_string['bymonth'] = recurrence['by_month']
        elif recurrence['by_year_day']:
            rec_ics_string['byyearday'] = recurrence['by_year_day']

    new_event.add('RRULE', rec_ics_string)
    return(new_event)

def mongo_to_ics(events):
    """
    creates the iCal based on the MongoDb database and events submitted
    """

    #initialize calendar object
    cal = Calendar()
    cal.add('PRODID', 'ABE')
    cal.add('VERSION', '2.0')
    for event in events:
        new_event = create_ics_event(event) # create the base event fields in ics format

        recurrence = event['recurrence']
        if recurrence:
            new_event = create_ics_recurrence(new_event, recurrence) # create the rrule field

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


def ics_to_dict(component, labels, ics_id=None):
    """
    Converts an ics component to a dictionary that 
    can be used to create or update a mongoDB object

    component       The ics component representing a singular event

    labels          labels given

    ics_id          the objectId corresponding to the ICS object that 
                    this component comes from 
    """
    event_def = {}

    utc = pytz.utc
    convert_timezone = lambda a: a.astimezone(utc)

    event_def['title'] = str(component.get('summary'))
    event_def['description'] = str(component.get('description'))
    event_def['location'] = str(component.get('location'))

    event_def['start'] = convert_timezone(component.get('dtstart').dt)
    event_def['end'] = convert_timezone(component.get('dtend').dt)

    event_def['labels'] = labels
    
    if component.get('recurrence-id'): # if this is the ics equivalent of a sub_event
        event_def['rec_id'] = convert_timezone(component.get('recurrence-id').dt)
    else: # if this is a normal event or a parent event
        event_def['ics_id'] = ics_id

    event_def['UID'] = str(component.get('uid'))

    if component.get('rrule'): # if this is an event that defines a recurrence
        rrule = component.get('rrule')
        rec_def = {}
        rec_def['frequency'] = str(rrule.get('freq')[0])
        if 'until' in rrule:
            rec_def['until'] = convert_timezone(rrule.get('until')[0])
        elif 'count' in rrule:
            rec_def['count'] = str(rrule.get('count')[0])
        else:
            event_def['forever'] = True
        if 'BYDAY' in rrule:
            rec_def['by_day'] = rrule.get('BYDAY')
        if 'BYMONTHDAY' in rrule:
            rec_def['by_month_day'] = rrule.get('BYMONTHDAY')
        if 'INTERVAL' in rrule:
            rec_def['interval'] = str(rrule.get('INTERVAL')[0])
        else:
            rec_def['interval'] = '1'

        event_def['recurrence'] = rec_def
    return(event_def)
    

def extract_ics(cal, ics_url, labels=None):
    """
    Extracts the ics components and stores them 

    cal         the ics calendar

    ics_url     the ics feed url

    labels      labels to assign to the events
    """
    results = db.ICS.objects(url=ics_url).first()
    logging.debug("ics feeds: {}".format(mongo_to_dict(results)))
    
    if results: # if this feed has already been inputted
        for component in cal.walk():
            if component.name == "VEVENT":
                last_modified = component.get('LAST-MODIFIED').dt
                now = datetime.now(timezone.utc)
                difference = now - last_modified
                # if an event has been modified in the last two hours
                if difference.total_seconds() < 7200: 
                    update_ics_to_mongo(component, results.labels)
    else: # if this is the first time this ics feed has been inputted
        # save the ics url feed as an ICS object
        ics_object = db.ICS(**{'url':ics_url, 'labels':labels}).save()
        temporary_dict = []
        for component in cal.walk():
            if component.name == "VEVENT":
                # convert the event to a dictionary
                com_dict = ics_to_dict(component, labels, ics_object.id)

                if 'rec_id' in com_dict: # if this is a sub_event
                    # search for another event with the same UID
                    normal_event = db.Event.objects(__raw__ = {'UID':com_dict['UID']}).first()
                    if normal_event is not None: # if its parent event has already been created
                        create_sub_event(com_dict, normal_event)
                        logging.debug("sub event created in new instance")
                    else: # if its parent event has not been created
                        # store the dict in a list to come back to later
                        temporary_dict.append(com_dict)
                        logging.debug("temporarily saved recurring event as dict")
                else: # if this is a regular event
                    new_event = db.Event(**com_dict).save()
                    if new_event.labels == []: # if the event has no labels
                        new_event.labels = ['unlabeled']
                    if 'recurrence' in new_event: # if the event has no recurrence_end
                        if new_event.recurrence.forever == False:
                            new_event.recurrence_end = find_recurrence_end(new_event)
                            logging.debug("made end_recurrence: {}".format(new_event.recurrence_end))
                    new_event.save()

        # cycle through all the events in the temporary list
        for sub_event_dict in temporary_dict:
            normal_event = db.Event.objects(__raw__ = {'UID':sub_event_dict['UID']}).first()
            create_sub_event(sub_event_dict, normal_event)
            logging.debug("temporarily put off sub_event now saved as mongodb object")
                

def update_ics_to_mongo(component, labels):
    """
    Updates the mongoDB database with an ical component
    """
    # find the event with this UID
    normal_event = db.Event.objects(__raw__ = {'UID' : str(component.get('UID'))}).first()
    if component.get('recurrence-id'): # if this is the ics equivalent of a sub_event
        # check to see if a sub_event with the rec_id and UID already exists
        parent_sub_event = db.Event.objects(__raw__ = 
            {'$and' : [
                {'sub_events.rec_id' : component.get('recurrence-id').dt},
                {'UID' : str(component.get('UID'))}]}).first()
        logging.debug("parent event found for reccurrence-id: {}".format(component.get('recurrence-id').dt))
    else:
        parent_sub_event = None
    event_dict = ics_to_dict(component, labels)
    if parent_sub_event: # if the sub_event already exists
        logging.debug("sub event updated")
        update_sub_event(event_dict, parent_sub_event,event_dict['rec_id'], True)
    elif normal_event: # if the sub_event doesn't already exist
        if component.get('recurrence-id'): # if this is a sub_event
            logging.debug("new sub event created")
            create_sub_event(event_dict, normal_event)
        else: # if this is a normal_event
            logging.debug("normal event updated")
            normal_event.update(**event_dict)
            normal_event.reload()      
    else: # if this is a new event entirely
        logging.debug("normal event created")
        db.Event(**event_dict).save()
        

def update_ics_feed():
    """
    updates the mongoDB database based on all the ics feeds tored in ICS
    called by the celery worker every 2 hours
    """
    all_ics_feeds = db.ICS.objects(__raw__ = {})
    for feed in all_ics_feeds:
        data = requests.get(feed['url'].strip()).content.decode('utf-8')
        cal = Calendar.from_ical(data)
        extract_ics(cal, feed['url'])