###
# Copyright (c) 2013, None
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import conf
from supybot import ircmsgs

import sqlite3
import os.path

class UserSettingsDB(object):
    def __init__(self, filename):
        self.filename = filename
        self.db = None

    def _commit(self):
        '''a commit wrapper to give it another few tries if it errors.
        
        which sometimes happens due to:
        OperationalError: database is locked'''
        for i in xrange(10):
            try:
                self.db.commit()
            except:
                time.sleep(1)

    def open(self):
        if os.path.exists(self.filename):
            db = sqlite3.connect(self.filename, check_same_thread = False)
            db.text_factory = str
            self.db = db
            return
        
        db = sqlite3.connect(self.filename, check_same_thread = False)
        db.text_factory = str
        self.db = db
        cursor = self.db.cursor()

        cursor.execute("""CREATE TABLE rating_notification (
                          id INTEGER PRIMARY KEY,
                          user_id INTEGER,
                          nick TEXT UNIQUE ON CONFLICT REPLACE)
                          """)
        self._commit()
        return

    def close(self):
        self.db.close()

    def addRatingNotification(self, userId, nick):
     	cursor = self.db.cursor()
      	cursor.execute("""INSERT INTO rating_notification VALUES (NULL, ?, ?)""", (userId, nick))
      	self._commit()

    def removeRatingNotification(self, userId, nick):
      	cursor = self.db.cursor()
      	cursor.execute("""DELETE FROM rating_notification WHERE user_id = ?""", (userId,))
      	self._commit()

    def getRatedNick(self, userId):
        cursor = self.db.cursor()
        cursor.execute("""SELECT nick FROM rating_notification WHERE user_id = ?""", (userId,))
        return cursor.fetchall()




class UserSettings(callbacks.Plugin):
    """This plugin is just to save in a db information about
    the user. For example, The RatingSystem plugin uses
    UserSettings to save if the user wants a notification
    every time he/she gets rated."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(UserSettings, self)
        self.__parent.__init__(irc)
        self.filename = conf.supybot.directories.data.dirize('UserSettings.db')
        self.db = UserSettingsDB(self.filename)
        self.db.open()

    def die(self):
        self.__parent.die()
        self.db.close()

    def _addRatingNotification(self, userId, nick):
        self.db.addRatingNotification(userId, nick)

    def _removeRatingNotification(self, userId, nick):
        self.db.removeRatingNotification(userId, nick)

    def _getRatedNick(self, userId):
        return self.db.getRatedNick(userId)

Class = UserSettings


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
