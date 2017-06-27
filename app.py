#!/usr/bin/env python3
"""Main flask app"""
from flask import Flask, render_template
from flask_restful import Api
from flask_cors import CORS
import os

import logging
FORMAT = "%(levelname)s:ABE: _||_ %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

from resource_models import EventApi, LabelApi, ICSFeed

app = Flask(__name__)
CORS(app)
api = Api(app)

# Route resources
api.add_resource(EventApi, '/events/', methods=['GET', 'POST'], endpoint='event')
api.add_resource(EventApi, '/events/<string:event_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], endpoint='event_id')  # TODO: add route for string/gphycat links

api.add_resource(LabelApi, '/labels/', methods=['GET', 'POST'], endpoint='label')
api.add_resource(LabelApi, '/labels/<string:label_name>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], endpoint='label_name')

api.add_resource(ICSFeed, '/ics/', methods=['GET', 'POST'], endpoint='ics')
api.add_resource(ICSFeed, '/ics/<string:ics_name>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], endpoint='ics_name')


@app.route('/')
def splash():
    return render_template('splash.html')


@app.route('/add_event')
def add_event():
    return render_template('add_event.html')


@app.route('/add_label')
def add_label():
    return render_template('add_label.html')


if __name__ == '__main__':
    app.debug = os.getenv('FLASK_DEBUG', True) # updates the page as the code is saved
    HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT)
