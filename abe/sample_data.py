#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sample data that can be added to the database"""
from datetime import datetime
from dateutil import parser

sample_events = [
    {
        "visibility": "olin",
        'title': 'Coffee Break',
        'location': 'Quiet Reading Room',
        'description': 'Fika (Swedish pronunciation: [²fiːka]) is a concept in Swedish (and Finnish) culture with the basic meaning "to have coffee", often accompanied with pastries, cookies or pie.',
        'start': datetime(2017, 6, 1, 19),
        'end': datetime(2017, 6, 1, 19, 30),
        'recurrence_end': datetime(2017, 7, 31),
        "labels": ["summer", "library", "owl"],
        'recurrence': {
            'frequency': 'WEEKLY',
            'interval': '1',
            'until': datetime(2017, 7, 31),
            'by_day': ["MO", "TU", "WE", "TH", "FR"]
        }
    },
    {
        "visibility": "olin",
        "title": "Extended Productivity Session",
        "location": "Library",
        "start": datetime(2017, 7, 13, 21),
        "end": datetime(2017, 7, 14, 4),
        "labels": ["summer", "library", "owl", 'featured'],
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
        "title": "Bowling!",
        "start": datetime(2017, 6, 27, 21, 0),
        "end": datetime(2017, 6, 27, 23, 0),
        "description": 'Drive/Carpool to Lanes and Games\n- Appetizers\n- Pizza\n- Bowling\n- Etc.',
        "location": "195 Concord Turnpike, Rte 2E\nCambridge, MA 02140",
        "labels": ['summer', 'library', 'potluck', 'featured'],
    },
    {
        "_cls": "Event",
        "title": "Midnight Memes",
        "description": "![now including surreal memes](https://i.imgur.com/I1Nvebi.jpg)",
        "location": "EH3nw",
        "start": parser.parse("2017-07-15T03:59:53Z"),
        "end": parser.parse("2017-07-15T05:00:53Z"),
        "visibility": "students",
        "labels": ["featured"],
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
    },
    {
        "name": "potluck",
    },
    {
        "name": "featured",
    }
]


def load_data(db, event_data=sample_events, label_data=sample_labels):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Inserting sample event data")
    for event in event_data:
        db.Event(**event).save()
    logging.info("Inserting sample label data")
    for label in label_data:
        db.Label(**label).save()


if __name__ == '__main__':  # import data
    from . import database as db
    load_data(db)
