#!/usr/bin/env python3
"""Document models for mongoengine"""
from mongoengine import *
from bson import ObjectId

class ICS(Document):
	"""
	Model for links to ics feeds
	These links are accessed by the celery worker to refresh the calendar from the ics feeds

	Fields:
	url 			Stores the link to an ics feed. Required
					Takes a stringfield

	"""
	url = StringField()