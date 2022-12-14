
# ---------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon.
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.itvx
# ---------------------------------------------------------------------------------------------------------------------

from test.support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import MagicMock, patch
import types

from test.support.testutils import open_json, open_doc
from test.support.object_checks import has_keys

from resources.lib import itvx

setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class MainPageItem(TestCase):
    @patch('resources.lib.fetch.get_document', new=open_doc('html/index.html'))
    def test_list_main_page_items(self):
        items = list(itvx.main_page_items())
        pass


class Collections(TestCase):
    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/index-data.json'))
    def test_collection_news(self, _):
        items = list(itvx.collection_content(slider='newsShortformSliderContent'))
        self.assertGreater(len(items), 10)
        for item in items:
            has_keys(item, 'playable', 'show')

    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/index-data.json'))
    def test_collection_trending(self, _):
        items = list(itvx.collection_content(slider='trendingSliderContent'))
        self.assertGreater(len(items), 10)
        for item in items:
            has_keys(item, 'playable', 'show')

    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/index-data.json'))
    def test_collection_from_main_page(self, _):
        items = list(itvx.collection_content(slider='editorialRailSlot1'))
        self.assertGreater(len(items), 10)
        for item in items:
            has_keys(item, 'playable', 'show')

    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/collection_just-in_data.json'))
    def test_collection_from_collection_page(self, _):
        items = list(itvx.collection_content(url='collection_top_picks'))
        self.assertGreater(len(items), 10)
        for item in items:
            has_keys(item, 'playable', 'show')

    @patch('resources.lib.itvx.get_page_data', side_effect=(open_json('html/collection_the-costume-collection.json'),
                                                            open_json('html/collection_the-costume-collection.json')))
    def test_collection_with_paid_items(self, _):
        # The costume collection has 18 show, 1 title, of which 3 are premium
        items = list(itvx.collection_content(url='the_costume_collection'))
        self.assertEqual(19, len(items))
        items = list(itvx.collection_content(url='the_costume_collection', hide_paid=True))
        self.assertEqual(16, len(items))



class Categories(TestCase):
    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/categories_data.json'))
    def test_get_categories(self, _):
        cat_list = list(itvx.categories())
        self.assertEqual(8, len(cat_list))

    @patch('resources.lib.itvx.get_page_data', side_effect=(open_json('html/category_children.json'),
                                                            open_json('html/category_drama-soaps.json'),
                                                            open_json('html/category_factual.json')))
    def test_get_category_content(self, _):
        for _ in range(3):
            program_list = list(itvx.category_content('asdgf'))
            self.assertGreater(len(program_list), 10)
            playables = 0
            for progr in program_list:
                has_keys(progr['show'], 'label', 'info', 'art', 'params')
                if progr['playable']:
                    playables +=1
            self.assertGreater(playables, 0)
            self.assertLess(playables, len(program_list) / 2)


    @patch('resources.lib.itvx.get_page_data', return_value=open_json('html/category_films.json'))
    def test_category_films(self, _):
        program_list = list(itvx.category_content('asdgf'))
        self.assertGreater(len(program_list), 10)
        for progr in program_list:
            has_keys(progr['show'], 'label', 'info', 'art', 'params')
            self.assertTrue(progr['playable'])
        free_list = list(itvx.category_content('asdgf', hide_paid=True))
        self.assertLess(len(free_list), len(program_list))


class Episodes(TestCase):
    @patch('resources.lib.fetch.get_document', new=open_doc('html/series_miss-marple.html'))
    def test_episodes_marple(self):
        series_listing = itvx.episodes('asd')
        self.assertIsInstance(series_listing, dict)
        self.assertEqual(len(series_listing), 6)


class Search(TestCase):
    @patch('resources.lib.fetch.get_json', return_value=open_json('search/the_chase.json'))
    def test_simple_search(self, _):
        result = itvx.search('the_chase')
        self.assertIsInstance(result, types.GeneratorType)
        self.assertEqual(10, len(list(result)))

    @patch('resources.lib.fetch.get_json', return_value=None)
    def test_search_without_results(self, _):
        result = itvx.search('xprs')
        self.assertIsNone(result)
