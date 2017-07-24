#!/usr/bin/env python3
"""The world's leading test suite for ABE
This test suite requires a local mongodb instance and writes to/drops a
database named "abe-unittest" for testing.
"""
import os
import unittest
import flask
from pymongo import MongoClient
import logging
from .context import abe
from abe import sample_data
import pdb


class AbeTestCase(unittest.TestCase):

    def setUp(self):
        """Setup testing environment"""
        os.environ["DB_NAME"] = "abe-unittest"
        os.environ["MONGO_URI"] = ""
        import abe.app  # import abe after env so it inits correctly
        abe.app.app.debug = True  # enable debug to prevent https redirects
        self.app = abe.app.app.test_client()

    def tearDown(self):
        """Teardown testing environment"""
        client = MongoClient()
        client.drop_database(os.environ['DB_NAME'])  # remove testing db
        client.close()

    def test_empty_db(self):
        event_response = self.app.get('/events/')
        label_response = self.app.get('/labels/')
        assert flask.json.loads(event_response.data) == []
        assert flask.json.loads(label_response.data) == []

    def test_add_sample_events(self):
        """Adds the sample events to the database"""
        for event in sample_data.sample_events:
            response = self.app.post(
                '/events/',
                data=flask.json.dumps(event),  # use flask.json for datetimes
                content_type='application/json'
            )
            assert response._status_code == 201  # check only status code

    def test_add_sample_labels(self):
        """Adds the sample labels to the database"""
        for event in sample_data.sample_labels:
            response = self.app.post(
                '/labels/',
                data=flask.json.dumps(event),
                content_type='application/json'
            )
            assert response._status_code == 201


if __name__ == '__main__':
    unittest.main()
