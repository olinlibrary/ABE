#!/usr/bin/env python3
"""Document models for mongoengine"""
from mongoengine import *

VISIBILITY = ['public', 'olin', 'students']

class RecurringEventDefinition(EmbeddedDocument):
    """Model for recurring events"""
    frequency = StringField(required=True)
    interval = StringField(required=True)
    count = StringField()
    until = DateTimeField()
    by_day = ListField(StringField())
    by_month_day = StringField()
    by_month = StringField()


class RecurringEventExc(EmbeddedDocument):  # TODO: get a better name
    """Model for Exceptions to recurring events"""
    sid = StringField()
    title = StringField()
    location = StringField()
    description = StringField()
    start = DateTimeField()
    end = DateTimeField()
    url = URLField()
    email = EmailField()
    rec_id = DateTimeField()
    deleted = BooleanField(default=False)


class Event(Document):
    """Standard model for events"""  # TODO: improve description
    title = StringField(required=True)  # TODO: set length limit
    description = StringField()  # TODO: set length limit
    location = StringField()  # TODO: check for olin naming conventions (WH225, AC120, 2NN)
    url = URLField()
    email = EmailField()  # TODO: Add whitelist?

    start = DateTimeField(required=True)
    end = DateTimeField()

    end_recurrence = DateTimeField()

    visibility = StringField(default='olin', choices=VISIBILITY)
    labels = ListField(StringField(), default=['unlabeled'])  # TODO: max length of label names?

    recurrence = EmbeddedDocumentField(RecurringEventDefinition)
    sub_events = ListField(EmbeddedDocumentField(RecurringEventExc))

    meta = {'allow_inheritance': True}  # TODO: set indexes

    # TODO: look into clean() function for more advanced data validation

class Label(Document):
    """Model for labels of events"""
    name = StringField(required=True, unique=True)  # TODO: set to primary key?
    description = StringField()
    url = URLField()
