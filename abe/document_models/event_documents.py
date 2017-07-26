#!/usr/bin/env python3
"""Document models for mongoengine"""
from mongoengine import *
from bson import ObjectId

VISIBILITY = ['public', 'olin', 'students']

class RecurringEventDefinition(EmbeddedDocument):
    """
    Represents the definition of a recurring event. Is stored as an embedded document of Event with the field 'recurrence'
    The definition is based off of the ics format. For more see: http://www.kanzaki.com/docs/ical/rrule.html

    Certain fields must be used with others and some cannot be used with others. See the link above for more information.

    Fields:
    frequency       The frequency of an event. Required.
                    Takes a string from a list of choices ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY')
                    Example: 'WEEKLY' (event occurs every week)

    interval        The interval between events. Required.
                    Takes a string of an integer. 
                    Example: '2' (would be every 2 days, 2 weeks, 2 months, or 2 years depending on frequency)

    count           How many events should occur. Optional.
                    Takes a string of an integer. 'Until' and 'count' cannot both be used.
                    Example: '6' (event occurs 6 times)

    until           Date at which event should stop occuring. Optional
                    Takes a datetime object. 'Until' and 'count' cannot both be used.
                    Example: datetime(2017, 7, 31) (event stops occuring on July 31, 2017)

    by_day          Which day of the week an event should occur. Optional
                    Takes a list of strings from a list of choices ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
                    Example: ["TU", "FR"] (event occurs every Tuesday and Friday)

    by_month_day    Which day of the month an event should occur. Optional
                    Takes a string of an integer
                    Example: '20' (event occurs on the 20th of a month)

    by_month        Which month an event should occur in. Optional
                    Takes a list of strings of integers from 1 through 12
                    Example: ['6', '7'] (event occurs in June and July)

    by_year_day     Which day of the year an event should occur on. Optional
                    Takes a list of strings of integers from 1 through 365
                    Example: ['1', '100', '200'] (event occurs on the 1rst, 100th, and 200th day of the year)

    forever         Indicates whether this recurrence has an end. Optional to define, but will default to False
                    Takes a boolean
                    Example: True (True indicates this event goes on forever)

    """
    frequency = StringField(required=True)
    interval = StringField(required=True)
    count = StringField()
    until = DateTimeField()
    by_day = ListField(StringField())
    by_month_day = ListField(StringField())
    by_month = ListField(StringField())
    by_year_day = ListField(StringField())

    forever = BooleanField(default=False)


class RecurringEventExc(EmbeddedDocument):  # TODO: get a better name
    """
    Represents the definition of an event that is part of a recurring series, but has been
    edited to be different from the series. This definition will be stored as an embedded document
    in the recurring event field "sub_events".
    These events are referred to as a sub_event.

    This class only saves the fields that are explicitly different from its parent event.
    When sending this event in the API, the fields that have not been changed (so they're not saved
    in this object), will inherit from the parent event.

    Fields:
    sid             The id of the parent of the sub_event. Required
                    Inherits the id of its Event parent

    rec_id          The start datetime of the event had it not been edited. Required
                    Takes a datetime
                    Example: If the recurring event was supposed to occur on July 5th at 5pm, but has 
                    since been edited to occur on July 5th at 6pm, rec_id will be datetime(2017, 7, 5, 5)

    _id             The id of the sub_event. Required
                    Takes an ObjectID object
                    Generated using the MongoDB bson ObjectId library

    UID             id given to sub_event from an ics file. This id acts like an sid for objects in ICS files
                    Takes a string

    title           Title of the sub_event. Optional
                    Takes a string
                    Example: "SLAC"

    location        Location of the event. Optional
                    Takes a string
                    Example: "Library Upper Level"

    description     Description of the event. Optional
                    Takes a string
                    Example: "This event will have food and dancing"

    url             Url field for the event. Optional (currently not used in fullcalendar)
                    Takes a URL

    email           Email field for the event. Optional (currently not used in fullcalendar)
                    Takes an email address

    labels          Labels for the events. Optional
                    Takes a list of strings which choice from the labels database
                    Example: ["Library", "STAR"]

    start           Start datetime of the event. Optional
                    Takes a datetime object
                    Example: datetime(2017, 9, 06, 20)

    end             End datetime of the event. Optional
                    Takes a datetime object
                    Example: datetime(2017, 9, 06, 23)

    allDay          Indicates whether this event is an all day event. Optional
                    Takes a boolean
                    Example: True (event runs all day)

    deleted         Indicates whether this event has been deleted. Required (defaults to False)
                    Takes a boolean
                    Example: True (event has been deleted)

    meta            Indexes certain fields to make querying more efficient

    """
    sid = StringField()
    rec_id = DateTimeField()
    _id = ObjectIdField(default=ObjectId)
    UID = StringField()

    title = StringField()
    location = StringField()
    description = StringField()
    url = URLField()
    email = EmailField()

    labels = ListField(StringField())

    start = DateTimeField()
    end = DateTimeField()
    allDay = BooleanField(default=False)
    
    deleted = BooleanField(required=True, default=False)
    
    meta = {
        'indexes': [
            'sid',
            'rec_id',
            '_id'
        ]
    }


class Event(Document):
    """
    Description of an event. Can include embedded documents if it defines a recurring event

    Fields:
    _id             The id of the event. Required (we cannot change this value)
                    Takes an ObjectID object
                    Automatically generated using the MongoDB bson ObjectId library

    UID             id given to event from an ics file. This id acts like an sid for objects in ICS files
                    Takes a string

    ics_id          Links the event to an ics feed. Optional
                    Takes an ics feed link as a string. This string is also saved as an ICS document

    title           Title of the event. Required
                    Takes a string
                    Example: "SLAC"

    location        Location of the event. Optional
                    Takes a string
                    Example: "Library Upper Level"

    description     Description of the event. Optional
                    Takes a string
                    Example: "This event will have food and dancing"

    url             Url field for the event. Optional (currently not used in fullcalendar)
                    Takes a URL

    email           Email field for the event. Optional (currently not used in fullcalendar)
                    Takes an email address

    labels          Labels for the events. Optional
                    Takes a list of strings whith choice from the labels database
                    Example: ["Library", "STAR"]

    visibility      Indicates who can see this event. Optional (defaults to 'olin')
                    Takes a string from the list of choices VISIBILITY
                    Example: 'students' (only students can see this event)

    start           Start datetime of the event. Required
                    Takes a datetime object
                    Example: datetime(2017, 9, 06, 20)

    end             End datetime of the event. Optional
                    Takes a datetime object
                    Example: datetime(2017, 9, 06, 23)

    allDay          Indicates whether this event is an all day event. Optional (but defaults to False)
                    Takes a boolean
                    Example: True (event runs all day)

    recurrence      Definition of the recurrence. Optional
                    Takes a RecurringEventDefinition document

    recurrence_end  Indicates the day after the last event in the recurrence. Optional
                    Takes a datetime object. Will be filled automatically when a post request is made

    sub_events      Indicates the recurring event exceptions. Optional
                    Takes a RecurringEventExc document

    meta            Indexes certain fields to make querying more efficient
    """
    UID = StringField()
    ics_id = ObjectIdField()

    title = StringField(required=True)  # TODO: set length limit
    description = StringField()  # TODO: set length limit
    location = StringField()  # TODO: check for olin naming conventions (WH225, AC120, 2NN)
    url = URLField()
    email = EmailField()  # TODO: Add whitelist?
    labels = ListField(StringField(), default=['unlabeled'])  # TODO: max length of label names?
    visibility = StringField(default='olin', choices=VISIBILITY)

    start = DateTimeField(required=True)
    end = DateTimeField()
    allDay = BooleanField(default=False)

    recurrence = EmbeddedDocumentField(RecurringEventDefinition)
    recurrence_end = DateTimeField()
    
    sub_events = EmbeddedDocumentListField(RecurringEventExc)
 
    meta = {'allow_inheritance': True,
        'indexes': [
            'start',
            'end',
            'recurrence_end']
        }

    # TODO: look into clean() function for more advanced data validation
