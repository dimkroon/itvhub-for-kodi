# ---------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022. Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.itvx
# ---------------------------------------------------------------------------------------------------------------------

import os
import string
import time
import logging

from datetime import datetime, timedelta
import pytz

from codequick import Script
from codequick.support import logger_id

from . import utils
from . import fetch
from . import kodi_utils

from .errors import AuthenticationError


logger = logging.getLogger(logger_id + '.itv')


def get_live_schedule(hours=4):
    """Get the schedule of the live channels from now up to the specified number of hours.

    """

    # Calculate current british time and the difference between that and local time
    btz = pytz.timezone('Europe/London')
    british_now = datetime.now(btz)
    local_offset = datetime.now() - datetime.utcnow()
    time_dif = local_offset - british_now.utcoffset()
    # in the above calculation we lose a few nanoseconds, so we need to convert the difference to round seconds again
    time_dif = timedelta(time_dif.days, time_dif.seconds + 1)

    # Request TV schedules for the specified number of hours from now, in british time
    from_date = british_now.strftime('%Y%m%d%H%M')
    to_date = (british_now + timedelta(hours=hours)).strftime('%Y%m%d%H%M')
    # Note: platformTag=ctv is exactly what a webbrowser sends
    url = 'https://scheduled.oasvc.itv.com/scheduled/itvonline/schedules?from={}&platformTag=ctv&to={}'.format(
        from_date, to_date
    )
    data = fetch.get_json(url)

    schedules_list = data.get('_embedded', {}).get('schedule', [])
    schedule = [element['_embedded'] for element in schedules_list]

    # convert British start time to local time
    for channel in schedule:
        for program in channel['slot']:
            time_str = program['startTime'][:16]
            # datetime.datetime.strptime has a bug in python3 used in kodi 19: https://bugs.python.org/issue27400
            brit_time = datetime(*(time.strptime(time_str, '%Y-%m-%dT%H:%M')[0:6]))
            loc_time = brit_time + time_dif
            program['startTime'] = loc_time.strftime('%H:%M')
            program['orig_start'] = program['onAirTimeUTC'][:19]

    return schedule


stream_req_data = {
    'client': {
        'id': 'browser',
        'supportsAdPods': False,
        'version': '4.1'
    },
    'device': {
        'manufacturer': 'Firefox',
        'model': '105',
        'os': {
            'name': 'Linux',
            'type': 'desktop',
            'version': 'x86_64'
        }
    },
    'user': {
        'entitlements': [],
        'itvUserId': '',
        'token': ''
    },
    'variantAvailability': {
        'featureset': {
            'max': ['mpeg-dash', 'widevine', 'outband-webvtt'],
            'min': ['mpeg-dash', 'widevine', 'outband-webvtt']
        },
        'platformTag': 'dotcom'
    }
}


def _request_stream_data(url, stream_type='live', retry_on_error=True):
    from .itv_account import itv_session
    session = itv_session()

    try:
        stream_req_data['user']['token'] = session.access_token
        stream_req_data['client']['supportsAdPods'] = stream_type != 'live'

        if stream_type == 'live':
            accept_type = 'application/vnd.itv.online.playlist.sim.v3+json'
            # Live MUST have a featureset containing an item without outband-webvtt, or a bad request is returned.
            min_features = ['mpeg-dash', 'widevine']
        else:
            accept_type = 'application/vnd.itv.vod.playlist.v2+json'
            #  ITV appears now to use the min feature for catchup streams, causing subtitles
            #  to go missing if not specfied here. Min and max both specifying webvtt appears to
            # be no problem for catchup streams that don't have subtitles.
            min_features = ['mpeg-dash', 'widevine', 'outband-webvtt']

        stream_req_data['variantAvailability']['featureset']['min'] = min_features

        stream_data = fetch.post_json(
            url, stream_req_data,
            headers={'Accept': accept_type},
            cookies=session.cookie)

        http_status = stream_data.get('StatusCode', 0)
        if http_status == 401:
            raise AuthenticationError

        return stream_data
    except AuthenticationError:
        if retry_on_error:
            if session.refresh():
                return _request_stream_data(url, stream_type, retry_on_error=False)
            else:
                if kodi_utils.show_msg_not_logged_in():
                    from xbmc import executebuiltin
                    executebuiltin('Addon.OpenSettings({})'.format(utils.addon_info['id']))
                return False
        else:
            raise


def get_live_urls(channel, url=None, title=None, start_time=None, play_from_start=False):
    """Return the urls to the dash stream, key service and subtitles for a particular live channel.

    .. Note::
        Subtitles are usually not available on live streams, but in order to be compatible with
        data returned by get_catchup_urls(...) None is returned.

    """
    # import web_pdb; web_pdb.set_trace()

    if url is None:
        url = 'https://simulcast.itv.com/playlist/itvonline/' + channel

    stream_data = _request_stream_data(url)
    video_locations = stream_data['Playlist']['Video']['VideoLocations'][0]
    dash_url = video_locations['Url']
    start_again_url = video_locations.get('StartAgainUrl')

    if start_again_url:
        if start_time and (play_from_start or kodi_utils.ask_play_from_start(title)):
            dash_url = start_again_url.format(START_TIME=start_time)
            logger.debug('get_live_urls - selected play from start at %s', start_time)
        else:
            # Go 20 sec back to ensure we get the timeshift stream
            start_time = datetime.utcnow() - timedelta(seconds=20)
            dash_url = start_again_url.format(START_TIME=start_time.strftime('%Y-%m-%dT%H:%M:%S'))

    key_service = video_locations['KeyServiceUrl']
    return dash_url, key_service, None


def get_catchup_urls(episode_url):
    """Return the urls to the dash stream, key service and subtitles for a particular catchup episode.
    """
    # import web_pdb; web_pdb.set_trace()
    stream_data = _request_stream_data(episode_url, 'catchup')['Playlist']['Video']
    url_base = stream_data['Base']
    video_locations = stream_data['MediaFiles'][0]
    dash_url = url_base + video_locations['Href']
    key_service = video_locations['KeyServiceUrl']
    try:
        # usually stream_data['Subtitles'] is just None when no subtitles are not available
        subtitles = stream_data['Subtitles'][0]['Href']
    except (TypeError, KeyError, IndexError):
        subtitles = None
    return dash_url, key_service, subtitles


def get_vtt_subtitles(subtitles_url):
    show_subtitles = Script.setting['subtitles_show'] == 'true'
    if show_subtitles is False:
        logger.info('Ignored subtitles by entry in settings')
        return None

    if not subtitles_url:
        logger.info('No subtitles available for this stream')
        return None

    # noinspection PyBroadException
    try:
        vtt_doc = fetch.get_document(subtitles_url)

        # vtt_file = os.path.join(utils.addon_info['profile'], 'subtitles.vtt')
        # with open(vtt_file, 'w', encoding='utf8') as f:
        #     f.write(vtt_doc)

        srt_doc = utils.vtt_to_srt(vtt_doc, colourize=Script.setting['subtitles_color'] != 'false')
        srt_file = os.path.join(utils.addon_info['profile'], 'subitles.srt')
        with open(srt_file, 'w', encoding='utf8') as f:
            f.write(srt_doc)

        return (srt_file, )
    except:
        logger.error("Failed to get vtt subtitles from url %s", subtitles_url, exc_info=True)
        return None

