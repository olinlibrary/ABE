#!/usr/bin/env python3
"""Test suite for sample_data.py
This test suite requires a local mongodb instance and writes to/drops a
database named "abe-unittest" for testing.
"""
import os
import unittest
from pymongo import MongoClient
import logging
from .context import abe
from abe import sample_data
import pdb


class SampleDataTestCase(unittest.TestCase):

    def setUp(self):
        """Setup testing environment"""
        os.environ["DB_NAME"] = "abe-unittest"
        os.environ["MONGO_URI"] = ""
        from abe import database as db
        self.db = db

    def tearDown(self):
        """Teardown testing environment"""
        client = MongoClient()
        client.drop_database(os.environ['DB_NAME'])  # remove testing db
        client.close()

    def test_load_data(self):
        """Load sample data"""
        sample_data.load_data(self.db)

if __name__ == '__main__':
    unittest.main()
