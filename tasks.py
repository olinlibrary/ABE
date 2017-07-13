from celery import Celery
import database as db
import time 

#Specify mongodb host and datababse to connect to
BROKER_URL = 'mongodb://localhost:27017/jobs'

celery = Celery('EOD_TASKS',broker=BROKER_URL)

#Loads settings for Backend to store results of jobs 
celery.config_from_object('celeryconfig')

@celery.task
def refresh_calendar():
	return("refreshing a calendar")