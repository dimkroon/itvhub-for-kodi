# ---------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022. Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.itvx
# ---------------------------------------------------------------------------------------------------------------------

import logging

import xbmcgui

from codequick import Script, utils
from codequick.support import addon_data, logger_id


logger = logging.getLogger(logger_id + '.kodi_utils')


TXT_LOG_TARGETS = 30112
TXT_ITV_ACCOUNT = 30200

TXT_MORE_INFO = 30604

TXT_ACCOUNT_ERROR = 30610
MSG_LOGIN = 30611
MSG_LOGIN_SUCCESS = 30612
MSG_LOGGED_OUT_SUCCESS = 30613

TXT_USERNAME = 30614
TXT_PASSWORD = 30615
TXT_INVALID_USERNAME = 30616
TXT_INVALID_PASSWORD = 30617
TXT_TRY_AGAIN = 30618
TXT_RESUME_FROM = 30619
TXT_PLAY_FROM_START = 30620
TXT_LOGIN_NOW = 30621

BTN_TXT_OK = 30790
BTN_TXT_CANCEL = 30791


def ask_credentials(username: str = None, password: str = None):
    """Ask the user to enter his username and password.
    Return a tuple of (username, password). Each or both can be empty when the
    user has canceled the operation.

    The optional parameters `username` and `password` will be used as the
    default values for the on-screen keyboard.

    """
    new_username = utils.keyboard(Script.localize(TXT_USERNAME), username or '')
    if new_username:
        hide_characters = not addon_data.getSettingBool('show_password_chars')
        new_password = utils.keyboard(Script.localize(TXT_PASSWORD), password or '', hidden=hide_characters)
    else:
        new_password = ''
    return new_username, new_password


def show_msg_not_logged_in():
    """Show a message to inform the user is not logged in and
    ask whether to login now.

    """
    dlg = xbmcgui.Dialog()
    result = dlg.yesno(
            Script.localize(TXT_ACCOUNT_ERROR),
            Script.localize(MSG_LOGIN),
            nolabel=Script.localize(BTN_TXT_CANCEL),
            yeslabel=Script.localize(TXT_LOGIN_NOW))
    return result


def show_login_result(success: bool, message: str = None):
    if success:
        icon = Script.NOTIFY_INFO
        if not message:
            message = Script.localize(MSG_LOGIN_SUCCESS)
    else:
        icon = Script.NOTIFY_WARNING

    Script.notify(Script.localize(TXT_ITV_ACCOUNT), message, icon)


def ask_login_retry(reason):
    """Show a message that login has failed and ask whether to try again"""

    if reason.lower() == 'invalid username':
        reason = Script.localize(TXT_INVALID_USERNAME)
    elif reason.lower() == 'invalid password':
        reason = Script.localize(TXT_INVALID_PASSWORD)

    msg = '\n\n'.join((reason, Script.localize(TXT_TRY_AGAIN)))

    dlg = xbmcgui.Dialog()

    return dlg.yesno(
            Script.localize(TXT_ACCOUNT_ERROR),
            msg,
            nolabel=Script.localize(BTN_TXT_CANCEL),
            yeslabel=Script.localize(BTN_TXT_OK))


def ask_log_handler(default):
    options = Script.localize(TXT_LOG_TARGETS).split(',')
    dlg = xbmcgui.Dialog()
    result = dlg.contextmenu(options)
    if result == -1:
        result = default
    try:
        return result, options[result]
    except IndexError:
        # default value is not necessarily a valid index.
        return result, ''


def ask_play_from_start(title=None):
    dlg = xbmcgui.Dialog()

    return dlg.yesno(
            title or 'ITVX',
            Script.localize(TXT_PLAY_FROM_START))
