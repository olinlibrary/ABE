#!/usr/bin/env python3
"""Document models for mongoengine"""
from mongoengine import *
from bson import ObjectId


class Label(Document):
    """
    Model for labels of events

    Fields:
    name 			Name of the label. Required and must be unique
    				Takes a string
    				Example: "Library"

    description 	Description of the label. Optional
    				Takes a string
    				Example: "Any event that has to do with the library"

    url 			A url to link to the label. Optional
    				Takes a url (not currently used by frontend)

    default 		Indicates to fullcalendar to display it by default. Suggestion
    				Takes a boolean
    				Example: True (fullcalendar will display the label by default)

    parent_labels 	Indicates which under which labels this label lives under. Optional
    				Takes a list of strings with choice from the Labels database

    color 			Suggested color for the lable. Optional
    				Takes a string (hex string currently works)

    visibility 		Indicates who can see the label. Optional
    				Takes a string
    """
    name = StringField(required=True, unique=True)  # TODO: set to primary key?
    description = StringField()
    url = URLField()
    default = BooleanField(required=True, default=False)  # suggested to display by default
    parent_labels = ListField(StringField())  # rudimentary hierarchy of labels
    color = StringField()  # suggested color for label
    visibility = StringField()  # suggested visibility
