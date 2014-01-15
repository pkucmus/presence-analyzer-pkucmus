# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, url_for, make_response
from flask.ext.mako import MakoTemplates, render_template
from mako.exceptions import TopLevelLookupException
from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, get_data, mean, \
    group_by_weekday, group_by_weekday_start_end, get_user_data

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

MAKO = MakoTemplates(app)


def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for('templateview', template_name='presence_weekday'))


@app.route('/')
@app.route('/<string:template_name>', methods=['GET'])
def templateview(template_name='site_base'):
    """
    Renders and response page by template name from url.
    """
    try:
        return render_template(template_name+'.html')
    except TopLevelLookupException:
        return make_response('This page does not exist', 404)


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def users_api2_view():
    """
    Users listing for dropdown new api.
    """
    return get_user_data()


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
            for i in data]


@app.route('/api/v1/presence_start_end/', methods=['GET'])
@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id=None):
    """
    Returns start and end time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday_start_end(data[user_id])

    result = [(
        calendar.day_abbr[weekday],
        mean(intervals['starts']),
        mean(intervals['ends']),
        )
        for weekday, intervals in weekdays.items()
    ]

    return result


@app.route('/api/v1/mean_time_weekday/', methods=['GET'])
@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id=None):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/', methods=['GET'])
@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id=None):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result
