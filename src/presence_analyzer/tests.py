# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_DATA_CSV_2 = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data_2.csv'
)
TEST_USERS_DATA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
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
        main.app.config.update({
            'DATA_CSV': TEST_DATA_CSV,
            'USER_DATA_XML': TEST_USERS_DATA,
        })
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
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome in presence analyzer", resp.data)

    def test_templateview_rendering(self):
        """
        Test page rendering with url given template name.
        """
        resp = self.client.get('/presence_start_end')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Presence start-end weekday", resp.data)
        resp = self.client.post('/presence_start_end')
        self.assertEqual(resp.status_code, 405)

        resp = self.client.get('/mean_time_weekday')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Presence mean time by weekday", resp.data)
        resp = self.client.post('/mean_time_weekday')
        self.assertEqual(resp.status_code, 405)

        resp = self.client.get('/presence_weekday')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Presence by weekday", resp.data)
        resp = self.client.post('/presence_weekday')
        self.assertEqual(resp.status_code, 405)

        resp = self.client.get('/not_existing_page')
        self.assertEqual(resp.status_code, 404)

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

    def test_new_api_users(self):
        """
        Test users xml api listing.
        """
        resp = self.client.get('/api/v2/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)['users']
        self.assertEqual(len(data), 3)
        self.assertDictEqual(data['141'], {
            u'name': u'Adam P.',
            u'avatar': u'/api/images/users/141'
        })

    def test_api_presence_start_end(self):
        """
        Test user weekday presence start end
        """
        resp = self.client.get('/api/v1/presence_start_end/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertItemsEqual(data, [
            [u'Mon', 33134, 57257],
            [u'Tue', 33590, 50154],
            [u'Wed', 33206, 58527],
            [u'Thu', 35602, 58586],
            [u'Fri', 47816, 54242],
            [u'Sat', 0, 0],
            [u'Sun', 0, 0],
        ])

    def test_api_presence_weekday(self):
        """
        Test user presence grouped by weekday api
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertItemsEqual(data, [
            [u'Weekday', u'Presence (s)'],
            [u'Mon', 0],
            [u'Tue', 30047],
            [u'Wed', 24465],
            [u'Thu', 23705],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0],
        ])

    def test_api_presence_meantime(self):
        """
        Test user meantime presence grouped by weekday api
        """
        resp = self.client.get('/api/v1/mean_time_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertItemsEqual(data, [
            [u'Mon', 24123.0],
            [u'Tue', 16564.0],
            [u'Wed', 25321.0],
            [u'Thu', 22984.0],
            [u'Fri', 6426.0],
            [u'Sat', 0],
            [u'Sun', 0],
        ])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({
            'DATA_CSV': TEST_DATA_CSV,
            'USER_DATA_XML': TEST_USERS_DATA,
        })

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_user_data(self):
        """
        Test parsing of user XML file.
        """
        data = utils.get_user_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ['users', 'server'])
        self.assertItemsEqual(data['users'].keys(), [176, 170, 141])
        self.assertDictEqual(data['users'][176], {
            u'name': u'Adrian K.',
            u'avatar': u'/api/images/users/176'
        })
        self.assertEqual(data['server'], u'https://intranet.stxnext.pl:443')

    def test_get_data_caching(self):
        """
        Test caching of get_data method.
        """
        data = utils.get_data()
        main.app.config.update({
            'DATA_CSV': TEST_DATA_CSV_2,
        })
        data_cached = utils.get_data()
        self.assertDictEqual(data, data_cached)

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
        self.assertItemsEqual(weekdays.keys(), range(7))
        self.assertDictEqual(weekdays, {
            0: [],
            1: [30047],
            2: [24465],
            3: [23705],
            4: [],
            5: [],
            6: [],
        })
        weekdays = utils.group_by_weekday(data[11])
        self.assertDictEqual(weekdays, {
            0: [24123],
            1: [16564],
            2: [25321],
            3: [22969, 22999],
            4: [6426],
            5: [],
            6: [],
        })

    def test_group_start_end_weekday(self):
        """
        Test weekday grouping start end
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday_start_end(data[11])
        self.assertItemsEqual(weekdays.keys(), range(7))
        self.assertSequenceEqual(weekdays, {
            0: {'starts': [33134], 'ends': [57257]},
            1: {'starts': [33590], 'ends': [50154]},
            2: {'starts': [33206], 'ends': [58527]},
            3: {'starts': [37116, 34088], 'ends': [60085, 57087]},
            4: {'starts': [47816], 'ends': [54242]},
            5: {'starts': [], 'ends': []},
            6: {'starts': [], 'ends': []},
        })

    def test_seconds_since_midnight(self):
        """
        Test seconds since midnight
        """
        self.assertEqual(utils.seconds_since_midnight(
            datetime.time(12, 45, 11)), 45911)
        self.assertEqual(utils.seconds_since_midnight(
            datetime.time(0, 0, 1)), 1)
        self.assertEqual(utils.seconds_since_midnight(
            datetime.time(15, 5, 19)), 54319)

    def test_interval(self):
        """
        Test interval calculation
        """
        self.assertEqual(utils.interval(
            datetime.time(12, 0, 0), datetime.time(13, 0, 0)), 3600)
        self.assertEqual(utils.interval(
            datetime.time(13, 0, 0), datetime.time(12, 30, 0)), -1800)
        self.assertEqual(utils.interval(
            datetime.time(4, 4, 4), datetime.time(1, 30, 0)), -9244)
        self.assertEqual(utils.interval(
            datetime.time(0, 0, 0), datetime.time(0, 0, 0)), 0)

    def test_mean(self):
        """
        Test mean calculation
        """
        self.assertEqual(utils.mean(range(1, 8)), 4)
        self.assertAlmostEqual(utils.mean([30.3, 70.2, 1]), 33.8333333)
        self.assertAlmostEqual(utils.mean([0.1, 0.2, 0.3]), 0.2)


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
