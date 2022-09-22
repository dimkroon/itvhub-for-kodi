# ------------------------------------------------------------------------------
#  Copyright (c) 2022. Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#
#  This file is part of plugin.video.itvhub
#
#  Plugin.video.itvhub is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or (at your
#  option) any later version.
#
#  Plugin.video.itvhub is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  plugin.video.itvhub. If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import os

from unittest.mock import patch


patch_g = None


def global_setup():
    """Fixture required for all test.
    Ensure this is imported and called in every test module first thing. At least before
    importing any other module from the project or other kodi related module.

    As it is global for all tests there is no need to tear down.
    """
    # Ensure that kodi's special://profile refers to a predefined folder. Just in case
    # some code want to write, whether intentional or not.
    global patch_g
    if patch_g is None:
        profile_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'addon_profile_dir'))
        patch_g = patch('xbmcaddon.Addon.getAddonInfo', new=lambda self, item: profile_dir if item == 'profile' else '')
        patch_g.start()


patch_1 = None


class RealWebRequestMadeError(Exception):
    pass


def setup_local_tests():
    """Module level fixture for all local tests. Ensures that no unintentional real
    web requests can occur.

    """
    global patch_1
    patch_1 = patch('requests.request', side_effect=RealWebRequestMadeError)
    patch_1.start()


def tear_down_local_tests():
    global patch_1
    if patch_1:
        patch_1.stop()
        patch_1 = None


def setup_web_test(*args):
    try:
        from test import account_login
        account_login.set_credentials()
    except ImportError:
        pass
