#!/usr/bin/env python3

import server

import json
import os
import tempfile
import unittest

class TestScheduler(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.db, server.app.config['DATABASE'] = tempfile.mkstemp()
        server.app.config['TESTING'] = True

    def test_get_schedule(self):
        print(server.get_schedule)

    def tearDown(self):
        os.close(self.db)
        os.unlink(server.app.config['DATABASE'])

if __name__ == "__main__":
    unittest.main()
