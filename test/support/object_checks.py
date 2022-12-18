# ---------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022. Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.itvx
# ---------------------------------------------------------------------------------------------------------------------

import time


def has_keys(dict_obj, *keys, obj_name='dictionary'):
    """Checks if all keys are present in the dictionary"""
    keys_set = set(keys)
    present_keys = set(dict_obj.keys()).intersection(keys_set)
    if present_keys != keys_set:
        absent = keys_set.difference(present_keys)
        raise AssertionError("Key{} {} {} not present in '{}'".format(
            's' if len(absent) > 1 else '',
            absent,
            'is' if len(absent) == 1 else 'are',
            obj_name)
        )


def misses_keys(dict_obj, *keys, obj_name='dictionary'):
    """Checks if all keys are NOT present in the dictionary"""
    keys_set = set(keys)
    present_keys = set(dict_obj.keys()).intersection(keys_set)
    if present_keys:
        raise AssertionError("Key{} {} should not be present in '{}'".format(
            's' if len(present_keys) > 1 else '',
            present_keys,
            obj_name)
        )


def is_url(url, ext=None):
    result = url.startswith('https://')
    if ext:
        result = result and url.endswith(ext)
    return result


def is_iso_time(time_str):
    """check if the time string is in the format like yyyy-mm-ddThh:mm:ssZ that is
    often used by itv's web services.
    Accept times with or without milliseconds
    """
    try:
        if '.' in time_str:
            time.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            time.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
        return True
    except ValueError:
        return False


def check_live_stream_info(playlist, additional_keys=None):
    """Check the structure of a dictionary containing urls to playlist and subtitles, etc.
    This checks a playlist of type application/vnd.itv.online.playlist.sim.v3+json, which is
    returned for live channels
    """
    mandatory_keys = ['Video', 'ProductionId', 'VideoType', 'ContentBreaks', 'Cdn']
    if additional_keys:
        mandatory_keys.update(additional_keys)
    has_keys(playlist, *mandatory_keys, obj_name='Playlist')

    video_inf = playlist['Video']
    has_keys(video_inf, 'Duration', 'Subtitles', 'Token', 'VideoLocations', obj_name="Playlist['Video']")

    assert isinstance(video_inf['Duration'], str)
    assert isinstance(video_inf['Subtitles'], (type(None), str))
    assert isinstance(video_inf['Token'], (type(None), str))

    strm_inf = video_inf['VideoLocations']
    assert isinstance(strm_inf, list), 'VideoLocations is not a list but {}'.format(type(strm_inf))
    for strm in strm_inf:
        assert (strm['Url'].startswith('https://') and '.mpd?' in strm['Url']), \
            "Unexpected playlist url: <{}>".format(strm['Url'])
        assert (strm['StartAgainUrl'].startswith('https://') and '.mpd?' in strm['StartAgainUrl']), \
            "Unexpected StartAgainUrl url: <{}>".format(strm['StartAgainUrl'])


def check_catchup_dash_stream_info(playlist, additional_keys=None):
    """Check the structure of a dictionary containing urls to playlist and subtitles, etc.
    This checks a playlist of type application/vnd.itv.vod.playlist.v2+json, which is
    returned for catchup productions
    """
    has_keys(playlist, 'Video', 'ProductionId', 'VideoType', 'ContentBreaks', obj_name='Playlist')

    video_inf = playlist['Video']
    has_keys(video_inf, 'Duration','Timecodes', 'Base', 'MediaFiles', 'Subtitles', 'Token', obj_name="Playlist['Video']")

    assert isinstance(video_inf['Duration'], str)
    assert isinstance(video_inf['Token'], (type(None), str))
    assert video_inf['Base'].startswith('https://') and video_inf['Base'].endswith('/')

    strm_inf = video_inf['MediaFiles']
    assert isinstance(strm_inf, list), 'MediaFiles is not a list but {}'.format(type(strm_inf))
    for strm in strm_inf:
        assert (not strm['Href'].startswith('https://')) and '.mpd?' in strm['Href'], \
            "Unexpected playlist url: <{}>".format(strm['Url'])
        assert strm['KeyServiceUrl'].startswith('https://'), \
            "Unexpected KeyServiceUrl url: <{}>".format(strm['StartAgainUrl'])
        assert isinstance(strm['KeyServiceToken'], str)

    subtitles = video_inf['Subtitles']
    assert isinstance(subtitles, (type(None),list)), 'MediaFiles is not a list but {}'.format(type(strm_inf))
    if subtitles is not None:
        for subt in subtitles:
            assert subt['Href'].startswith('https://') and subt['Href'].endswith('.vtt')
