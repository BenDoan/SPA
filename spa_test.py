#!/usr/bin/env python3

import server

import json
import os
import tempfile
import unittest
import logging

class TestScheduler(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.db, server.app.config['DATABASE'] = tempfile.mkstemp()
        server.app.config['TESTING'] = True
        logging.disable(logging.CRITICAL)

    def verify_courses(self, courses):
        self.assertTrue(len(courses) > 25)
        self.assertTrue(all(courses))

    def test_get_schedule(self):
        courses = server.get_schedule("Computer Science")
        flat_courses = [x for y in courses for x in y]
        self.verify_courses(flat_courses)

    def test_get_schedule_majors(self):
        courses = server.get_schedule("Computer Science")
        flat_courses = [x for y in courses for x in y]
        self.verify_courses(flat_courses)

        courses = server.get_schedule("Bioinformatics")
        flat_courses = [x for y in courses for x in y]
        self.verify_courses(flat_courses)

        courses = server.get_schedule("Information Assurance")
        flat_courses = [x for y in courses for x in y]
        self.verify_courses(flat_courses)

        courses = server.get_schedule("Management Information Systems")
        flat_courses = [x for y in courses for x in y]
        self.verify_courses(flat_courses)

    def login(self, username, password):
        return self.app.post('/signin', data=dict(
            name=username,
            password=password
        ), follow_redirects=True)

    def test_user(self):
        self.login('user', 'password')

    def tearDown(self):
        os.close(self.db)
        os.unlink(server.app.config['DATABASE'])

if __name__ == "__main__":
    unittest.main()
