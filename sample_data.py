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
        'by_day' : "MO"
        }
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
        'by_day' : "WE"
        }
    }

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
    }
]
