from celery import Celery
from abe.helpers import update_ics_feed
from abe import database as db
import time 
import logging

#Specify mongodb host and datababse to connect to
BROKER_URL = db.return_uri()

celery = Celery('EOD_TASKS',broker=BROKER_URL)

#Loads settings for Backend to store results of jobs 
celery.config_from_object('celeryconfig')

@celery.task
def refresh_calendar():
	update_ics_feed()
	return("did the stuff")