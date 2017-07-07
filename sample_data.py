#!/usr/bin/env python
"""Sample data that can be added to the database"""
from datetime import datetime

sample_events = [
  {
    "visibility": "olin",
    "title": "Coffee Break",
    "start": datetime(2017, 6, 14, 15, 0),
    "end": None,
    "description": 'Fika (Swedish pronunciation: [²fiːka]) is a concept in Swedish (and Finnish) culture with the basic meaning "to have coffee", often accompanied with pastries, cookies or pie.',
    "location": "Library",
    "labels": ['food', 'library'],
  },
  {
    "visibility": "public",
    "title": "OWL",
    "start": datetime(2017, 6, 15, 18, 30),
    "end": datetime(2017, 6, 15, 18, 30),
    "description": "Olin Workshop in the Library.\nTonight's topics include:\n- Pajama Jammy Jam reflections\n- parachute cleanup\n- workroom ideation",
    "location": "Library",
    "labels": ['clubs', 'OWL', 'library'],
  },
  {
    "visibility": "students",
    "title": "First Day of Work!",
    "start": datetime(2017, 6, 1, 9, 15),
    "end": datetime(2017, 6, 1, 17, 0),
    "description": 'Bring clothes to work/paint in',
    "location": "Library",
    "labels": ['summer', 'library'],
  },
  {
    "visibility": "olin",
    'title':'Book Club',
    'location': 'Quiet Reading Room',
    'description': 'reading cool books',
    'start': datetime(2017, 6, 19, 15),
    'end': datetime(2017, 6, 19, 16),
    'end_recurrence' : datetime(2017, 7, 31,0),
    "labels": ["summer", "library"],
    'recurrence' : {
        'frequency' : 'WEEKLY',
        'interval' : '1',
        'count' : '7',
        'by_day' : ["MO"]
        },
    'sub_events' : [
       {'title':'Not a club',
        'start': datetime(2017, 7, 3, 16), 
        'end': datetime(2017, 7, 3, 18),
        'rec_id': datetime(2017,7,3,15)
        },
        {'location': 'LOOOOOOOD',
        'description': 'reading NEWL BOOKS',
        'rec_id': datetime(2017,6,26,15)
        }
    ],
    },

    {
    "visibility": "olin",
    'title':'Newsch Celebration',
    'location': 'Library',
    'description': 'Doing cool newsch things',
    'start': datetime(2017, 6, 21, 15),
    'end': datetime(2017, 6, 21, 16),
    'end_recurrence' : datetime(2017, 7, 12,0),
    "labels": ["summer", "library"],
    'recurrence' : {
        'frequency' : 'WEEKLY',
        'interval' : '1',
        'count' : '4',
        'by_day' : ["WE"]
        }
    },
    {
    "visibility" : "olin",
    "title": "Bowling!",
    "start": datetime(2017, 6, 27, 17, 0),
    "end": datetime(2017, 6, 27, 19, 0),
    "description": 'Drive/Carpool to Lanes and Games\n- Appetizers\n- Pizza\n- Bowling\n- Etc.',
    "location": "195 Concord Turnpike, Rte 2E\nCambridge, MA 02140",
    "labels": ['summer', 'library', 'potluck'],
  },
]

sample_labels = [
    {
        "url": "http://library.olin.edu/",
        "name": "library",
        "description": "Events hosted in or relating to the Olin Library",
    },
    {
        "name": "food",
        "description": "Anything you can eat."
    },
    {
        "name": "clubs",
        "description": "Events hosted by or relating to Olin/BOW clubs and orgs"
    },
    {
        "name": "OWL",
        "description": "Olin Workshop in the Library"
    },
    {
        "name": "summer",
        "description": "Events happening over the summer."
    },
    {
        "name": "potluck",
    }
]

if __name__ == '__main__':  # import data
    import logging
    import database as db
    logging.info("Inserting sample event data")
    for event in sample_events:
        db.Event(**event).save()
    logging.info("Inserting sample label data")
    for label in sample_labels:
        db.Label(**label).save()
