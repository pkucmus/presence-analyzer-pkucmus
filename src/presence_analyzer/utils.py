# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import urllib2
import time
import threading
from json import dumps
from functools import wraps
from datetime import datetime
from lxml import etree

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

CACHE = {}
TIMESTAMPS = {}

LOCK = threading.Lock()


def memorize(key, period):
    """
    Memorizing decorator. Returning cached data
    if its validity period is not expired
    """
    def _decoration_wrapper(func):
        def _caching_wrapper(*args, **kwargs):
            cache_key = key
            now = time.time()

            if TIMESTAMPS.get(cache_key, now) > now:
                return CACHE[cache_key]

            ret = func(*args, **kwargs)
            CACHE[cache_key] = ret
            TIMESTAMPS[cache_key] = now + period
            return ret
        return _caching_wrapper
    return _decoration_wrapper


def locker(func):
    """
    Global thread locking decorator.
    """
    def _lock_wrapper(*args, **kwargs):
        with LOCK:
            ret = func(*args, **kwargs)
        return ret
    return _lock_wrapper


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def refresh_xml():
    """
    Download user XML data file from sargo server and save it as
    current config file.
    """
    req = urllib2.urlopen(app.config['XML_URL'])
    with open(app.config['USER_DATA_XML'], 'wb') as xmlfile:
        while True:
            chunk = req.read(16 * 1024)
            if not chunk:
                break
            xmlfile.write(chunk)


def get_user_data():
    """
    Extracts user data from file specified in config.
    """
    data = {}
    with open(app.config['USER_DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        root = tree.getroot()
        config = root[0]
        server = {
            u'host': unicode(config.findtext('host')),
            u'port': unicode(config.findtext('port')),
            u'protocol': unicode(config.findtext('protocol')),
        }
        data['server'] = "%(protocol)s://%(host)s:%(port)s" % server
        users = root[1]
        data['users'] = {
            int(user.attrib['id']): {
                u'name': unicode(user.findtext('name')),
                u'avatar': unicode(user.findtext('avatar'))
            }
            for user in users
        }
    return data


@locker
@memorize('get_data', 30)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_by_weekday_start_end(items):
    """
    Groups presence entries by weekday start end.
    """
    result = {i: {'starts': [], 'ends': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['starts'].append(
            seconds_since_midnight(start))
        result[date.weekday()]['ends'].append(
            seconds_since_midnight(end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
