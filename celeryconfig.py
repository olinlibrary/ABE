from datetime import timedelta

'''
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "jobs",
    "taskmeta_collection": "stock_taskmeta_collection",
}
'''

# used to schedule tasks periodically and passing optional arguments
# Can be very useful. Celery does not seem to support scheduled task but only periodic
CELERYBEAT_SCHEDULE = {
    'refresh-every-2-hours': {
        'task': 'tasks.refresh_calendar',
        'schedule': timedelta(seconds=7200),
    },
    'refresh-every-minute': {
        'task': 'tasks.parse_email_icals',
        'schedule': timedelta(seconds=60),
    }
}
