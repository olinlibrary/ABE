#!/usr/bin/env python3
"""Document models for mongoengine"""
from mongoengine import *

VISIBILITY = ['public', 'olin', 'students']


class Event(Document):
    """Standard model for events"""  # TODO: improve description
    title = StringField(required=True)  # TODO: set length limit
    description = StringField()  # TODO: set length limit
    location = StringField()  # TODO: check for olin naming conventions (WH225, AC120, 2NN)
    url = URLField()
    email = EmailField()  # TODO: Add whitelist?

    start = DateTimeField(required=True)
    end = DateTimeField()

    visibility = StringField(default='olin', choices=VISIBILITY)
    labels = ListField(StringField())  # TODO: max length of label names?

    meta = {'allow_inheritance': True}  # TODO: set indexes

    # TODO: look into clean() function for more advanced data validation


class RecurringEvent(Event):
    """Model for recurring events"""
    pass


class RecurringEventException(EmbeddedDocument):  # TODO: get a better name
    """Model for Exceptions to recurring events"""
    pass


class Label(Document):
    """Model for labels of events"""
    name = StringField(required=True, unique=True)  # TODO: set to primary key?
    description = StringField()
    url = URLField()
