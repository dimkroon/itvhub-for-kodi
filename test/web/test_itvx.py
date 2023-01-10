
# ---------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon.
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.itvx
# ---------------------------------------------------------------------------------------------------------------------


from test.support import fixtures
fixtures.global_setup()


import unittest

from typing import Generator

from codequick import Route

from resources.lib import itvx, errors
from test.support.object_checks import (is_url, has_keys, is_li_compatible_dict,
                                        check_catchup_dash_stream_info, check_live_stream_info)

setUpModule = fixtures.setup_web_test


@Route.register()
def dummycallback():
    pass


class TestItvX(unittest.TestCase):
    def test_get_now_next_schedule(self):
        result = itvx.get_now_next_schedule()
        for item in result:
            has_keys(item, 'name', 'channelType', 'streamUrl', 'images', 'slot')
        # print(json.dumps(result, indent=4))

    def test_get_live_channels(self):
        chan_list = list(itvx.get_live_channels())
        for item in chan_list:
            has_keys(item, 'name', 'channelType', 'streamUrl', 'images', 'slot')

    def test_get_categories(self):
        result = itvx.categories()
        self.assertIsInstance(result, Generator)
        for item in result:
            is_li_compatible_dict(self, item)

    def test_all_categories_content(self):
        categories = itvx.categories()
        for cat in categories:
            result = list(itvx.category_content(cat['params']['path']))
            self.assertGreater(len(result), 1)      # News has only a few items
            for item in result:
                self.assertIsInstance(item['playable'], bool)
                is_li_compatible_dict(self, item['show'])

    def test_search(self):
        items = itvx.search('the chase')
        self.assertGreater(len(list(items)), 2)
        items = itvx.search('xprgs')     # should return None or empty results, depending on how ITV responds.
        if items is not None:
            self.assertEqual(len(list(items)), 0)

    def test_get_playlist_url_from_episode_page(self):
        # legacy episode page, redirects to itvx https://www.itv.com/watch/holding/7a0203/7a0203a0002
        episode_url = 'https://www.itv.com/hub/holding/7a0203a0002'
        url = itvx.get_playlist_url_from_episode_page(episode_url)
        self.assertTrue(is_url(url))

        # itvx episode page - Nightwatch Series1 episode 2
        episode_url = "https://www.itv.com/watch/nightwatch/10a3249/10a3249a0002"
        url = itvx.get_playlist_url_from_episode_page(episode_url)
        self.assertTrue(is_url(url))

        # Premium episode Downton-abbey S1E1
        episode_url = "https://www.itv.com/watch/downton-abbey/1a8697/1a8697a0001"
        self.assertRaises(errors.AccessRestrictedError, itvx.get_playlist_url_from_episode_page, episode_url)

    def test__request_stream_data_vod(self):
        urls = (
            # something else with subtitles:
            'https://magni.itv.com/playlist/itvonline/ITV/10_0852_0001.001', )
        for url in urls:
            result = itvx._request_stream_data(url, 'vod')
            check_catchup_dash_stream_info(result['Playlist'])

    def test__request_stream_data_live(self):
        result = itvx._request_stream_data('https://simulcast.itv.com/playlist/itvonline/ITV', 'live')
        check_live_stream_info(result['Playlist'])