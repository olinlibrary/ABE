#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sample data that can be added to the database"""
from datetime import datetime
from dateutil import parser
import arrow


kelly_colors = ['#F2F3F4', '#222222', '#F3C300', '#875692', '#F38400', '#A1CAF1', '#BE0032', '#C2B280', '#848482', '#008856', '#E68FAC', '#0067A5', '#F99379', '#604E97', '#F6A600', '#B3446C', '#DCD300', '#882D17', '#8DB600', '#654522', '#E25822', '#2B3D26']

olin_colors = [#'#009BDF', '#A7A9AC', '#A7A9AC', '#000000',
    '#E31D3C', '#750324',
    '#F47920',
    '#FFC20E', '#C05131',
    '#C0D028',
    '#8EBE3F', '#00653E',
    '#349E49',
    # '#26AAA5', '#00677E',
    '#6BC1D3',
    '#009BDF', '#00458C',
    '#7B5AA6',
    '#C77EB5', '#511C74',
    '#ED037C'
]

sample_events = [
    {
        "visibility": "olin",
        'title': 'Coffee Break',
        'location': 'Quiet Reading Room',
        'description': 'Fika (Swedish pronunciation: [²fiːka]) is a concept in Swedish (and Finnish) culture with the basic meaning "to have coffee", often accompanied with pastries, cookies or pie.',
        'start': datetime(2017, 6, 1, 15),
        'end': datetime(2017, 6, 1, 15, 30),
        'recurrence_end': datetime(2017, 7, 31),
        "labels": ["summer", "library"],
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
        "start": datetime(2017, 7, 13, 17),
        "end": datetime(2017, 7, 14),
        "labels": ["summer", "library", "owl", 'featured'],
    },
    {
        "visibility": "public",
        "title": "OWL",
        "start": datetime(2017, 6, 15, 18, 30),
        "end": datetime(2017, 6, 15, 20),
        "description": "Olin Workshop in the Library.\nTonight's topics include:\n- Pajama Jammy Jam reflections\n- parachute cleanup\n- workroom ideation",
        "location": "Library",
        "labels": ['clubs', 'OWL', 'library', "testing"],
    },
    {
        "visibility": "students",
        "title": "First Day of Work!",
        "start": datetime(2017, 6, 1, 9, 15),
        "end": datetime(2017, 6, 1, 17, 0),
        "description": 'Bring clothes to work/paint in',
        "location": "Library",
        "labels": ['summer', 'library', "OWL", "SOS"],
    },
    {
        "visibility": "olin",
        "title": "Bowling!",
        "start": datetime(2017, 6, 27, 17, 0),
        "end": datetime(2017, 6, 27, 20, 0),
        "description": 'Drive/Carpool to Lanes and Games\n- Appetizers\n- Pizza\n- Bowling\n- Etc.',
        "location": "195 Concord Turnpike, Rte 2E\nCambridge, MA 02140",
        "labels": ['summer', 'library', 'potluck', "OWL", "SOS", 'featured'],
    },
    {
        "title": "Midnight Memes",
        "description": "![now including surreal memes](https://i.imgur.com/I1Nvebi.jpg)",
        "location": "EH3nw",
        "start": datetime(2017, 7, 15),
        "end": datetime(2017, 7, 15, 1),
        "visibility": "students",
        "labels": ["featured"],
    },
    {
        "title": "Aquaponics Meeting",
        "location": "Library workroom",
        "visibility": "students",
        "labels": ["featured"],
        'start': datetime(2017, 7, 1, 5),
        'end': datetime(2017, 7, 1, 7),
        'recurrence_end': datetime(2017, 8, 31),
        "labels": ["aquaponics", "clubs", "testing"],
        'recurrence': {
            'frequency': 'WEEKLY',
            'interval': '1',
            'until': datetime(2017, 8, 31),
            'by_day': ["SU"]
        }
    },
    {
        "title": "Candidate's Weekend",
        "visibility": "students",
        'start': datetime(2017, 7, 14),
        'end': datetime(2017, 7, 16),
        'allDay': True,
        'recurrence_end': datetime(2017, 7, 30),
        "labels": ["admissions", "featured", "testing"],
        'recurrence': {
            'frequency': 'WEEKLY',
            'interval': '1',
            'count': '3',
            'by_day': ["FR"]
        }
    },
    {
        "title": "Linedancing",
        "visibility": "students",
        "labels": ["featured", "testing"],
        'start': datetime(2017, 7, 1, 9),
        'end': datetime(2017, 7, 1, 11),
        'recurrence_end': datetime(2017, 7, 31),
        "labels": ["burstthebubble", "featured"],
        'recurrence': {
            'frequency': 'WEEKLY',
            'interval': '1',
            'until': datetime(2017, 8, 31),
            'by_day': ["SU"]
        }
    },
    {
        "title": "Bagel Breakfast",
        "start": datetime(2017, 8, 31),
        "end": datetime(2017, 8, 31),
        "labels": ["library", "food"]
    }
]

sample_labels = [
    {
        "url": "http://library.olin.edu/",
        "name": "library",
        "description": "Events hosted in or relating to the Olin Library",
        "color": "#26AAA5"
    },
    {
        "name": "food",
        "description": "Anything you can eat.",
        "default": True
    },
    {
        "name": "clubs",
        "description": "Events hosted by or relating to Olin/BOW clubs and orgs",
        "default": True
    },
    {
        "name": "classes",
        "default": True
    },
    {
        "name": "academic",
        "description": "Events from the academic calendar",
        "default": True
    },
    {
        "name": "STAR",
        "description": "Anything you can eat.",
        "default": True
    },
    {
        "name": "administration",
        "description": "Anything you can eat.",
        "default": True
    },
    {
        "name": "aquaponics",
        "parent_labels": ["clubs"]
    },
    {
        "name": "OWL",
        "description": "Olin Workshop in the Library"
    },
    {
        "name": "potluck",
        "description": "Events from Olin's hottest new library hackathon"
    },
    {
        "name": "summer",
        "description": "Events happening over the summer."
    },
    {
        "name": "featured",
        "default": True
    },
    {
        "name": "burstthebubble",
        "description": "Events outside of the Olin bubble.",
        "default": True
    },
    {
        "name": "testing",
        "description": "Sample events for testing"
    },
    {
        "name": "unlabeled",
        "description": "Events with the unlabeled label."
    }
]

sample_ics = [
    {
        "url": "webcal://http://www.olin.edu/calendar-node-field-cal-event-date/ical/calendar.ics"
    }
]


def load_data(
    db,
    event_data=sample_events,
    label_data=sample_labels,
    ics_data=sample_ics
):
    import logging
    from .helper_functions.sub_event_helpers import find_recurrence_end
    logging.basicConfig(level=logging.DEBUG)
    if event_data:
        logging.info("Inserting sample event data")
        for event in event_data:
            for key, value in event.items():
                if type(value) is datetime:  # convert to UTC from EST
                    og = value
                    event[key] = arrow.get(
                        value,
                        'US/Eastern'
                    ).to('utc').datetime
            new_event = db.Event(**event)
            if 'recurrence' in new_event:
                if new_event.recurrence.forever == False:
                    new_event.recurrence_end = find_recurrence_end(new_event)
                    logging.info("made some end recurrences: {}".format(new_event.recurrence_end))
            new_event.save()
    if label_data:
        logging.info("Inserting sample label data")
        for index, label in enumerate(label_data):
            if 'color' not in label:
                label['color'] = olin_colors[index]
            db.Label(**label).save()
    if ics_data:
        logging.info("Inserting sample ics data")
        for ics in ics_data:
            db.ICS(**ics).save()


if __name__ == '__main__':  # import data
    from . import database as db
    load_data(db)
