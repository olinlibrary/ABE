#!/usr/bin/env python3
"""Main flask app"""
from flask import Flask
from flask_restful import Api
import os

import logging
FORMAT = "%(levelname)s:ABE: _||_ %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

from resource_models import EventApi, LabelApi

app = Flask(__name__)
api = Api(app)

# Route resources
api.add_resource(EventApi, '/events/', methods=['GET', 'POST'], endpoint='event')
api.add_resource(EventApi, '/events/<string:event_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], endpoint='event_id')  # TODO: add route for string/gphycat links
api.add_resource(LabelApi, '/labels/', methods=['GET', 'POST'], endpoint='label')
api.add_resource(LabelApi, '/labels/<string:label_name>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], endpoint='label_name')

if __name__ == '__main__':
    app.debug = os.getenv('FLASK_DEBUG', True) # updates the page as the code is saved
    HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
    PORT = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=PORT)
