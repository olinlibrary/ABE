#!/usr/bin/env python3
"""Runs the Flask app"""
import os
from abe.app import app

# Configuration
app.debug = os.getenv('FLASK_DEBUG') != 'False'  # updates the page as the code is saved
app.config['REQUIRE_SSL'] = os.getenv('REQUIRE_SSL')
HOST = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
PORT = int(os.environ.get('PORT', 3000))

app.run(host='0.0.0.0', port=PORT)
