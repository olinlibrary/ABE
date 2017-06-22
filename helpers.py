#!/usr/bin/env python3
"""Miscellaneous helper functions of varying usefulness
helpful inspiration: https://gist.github.com/jason-w/4969476
"""
import pdb


def mongo_to_dict(obj):
    """Get dictionary from mongoengine object
    id is represented as a string
    """

    obj_dict = dict(obj.to_mongo())
    obj_dict['id'] = str(obj_dict['_id'])
    del(obj_dict['_id'])

    return obj_dict


def request_to_dict(request):
    """Convert incoming flask requests for objects into a dict"""
    req_dict = request.values.to_dict(flat=True)
    obj_dict = {k: v for k, v in req_dict.items() if v != ""}

    return obj_dict
