# ------------------------------------------------------------------------------
#  Copyright (c) 2022. Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#
#  This file is part of plugin.video.cinetree
#
#  Plugin.video.cinetree is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or (at your
#  option) any later version.
#
#  Plugin.video.cinetree is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  plugin.video.cinetree. If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import logging

from codequick import Script
from codequick.support import addon_data, logger_id

from resources.lib import itv_account
from resources.lib import kodi_utils
from resources.lib import logging as itv_logging

logger = logging.getLogger('.'.join((logger_id, __name__)))


@Script.register()
def login(_):
    # just to provide a route for settings' log in
    itv_account.session().login()


@Script.register()
def logout(_):
    # just to provide a route for settings' log out
    if itv_account.session().log_out():
        Script.notify(Script.localize(kodi_utils.TXT_ITV_ACCOUNT),
                      Script.localize(kodi_utils.MSG_LOGGED_OUT_SUCCESS),
                      Script.NOTIFY_INFO)


@Script.register()
def change_logger(_):
    """Callback for settings->generic->log_to.
    Let the user choose between logging to kodi log, to our own file, or no logging at all.

    """
    handlers = (itv_logging.KodiLogHandler, itv_logging.CtFileHandler, itv_logging.DummyHandler)

    try:
        curr_hndlr_idx = handlers.index(type(itv_logging.logger.handlers[0]))
    except (ValueError, IndexError):
        curr_hndlr_idx = 0

    new_hndlr_idx, handler_name = kodi_utils.ask_log_handler(curr_hndlr_idx)
    handler_type = handlers[new_hndlr_idx]

    itv_logging.set_log_handler(handler_type)
    addon_data.setSettingString('log-handler', handler_name)
