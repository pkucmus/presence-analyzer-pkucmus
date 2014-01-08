# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_presence_weekday(self):
        """
        Test user presence grouped by weekday
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(data[0], [u'Weekday', u'Presence (s)'])
        self.assertItemsEqual(data[1:], [[u'Mon', 0], [u'Tue', 30047], [u'Wed', 24465], [u'Thu', 23705], [u'Fri', 0], [u'Sat', 0], [u'Sun', 0]])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_group_by_weekday(self):
        """
        Test weekday grouping
        """
        data = utils.get_data()

        weekdays = utils.group_by_weekday(data[10])

        self.assertItemsEqual(weekdays.keys(), [0,1,2,3,4,5,6])
        self.assertEqual(weekdays[1][0], 30047)

    def test_seconds_since_midnight(self):
        """
        Test seconds since midnight
        """
        self.assertEqual(utils.seconds_since_midnight(datetime.time(12,45,11)), 45911)


    def test_interval(self):
        """
        Test interval calculation
        """
        self.assertEqual(utils.interval(datetime.time(12,0,0), datetime.time(13,0,0)), 3600)
        self.assertEqual(utils.interval(datetime.time(13,0,0), datetime.time(12,30,0)), -1800)

    def test_mean(self):
        """
        Test mean calculation
        """
        self.assertEqual(utils.mean([1,2,3,4,5,6,7]), 4)
        self.assertEqual(utils.mean([30.3,70.2,1]), 33.833333333333336)

def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
