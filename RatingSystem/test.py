###
# Copyright (c) 2010, Daniel Folkinshteyn
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

from supybot.test import *

import sqlite3
import time

class RatingSystemTestCase(PluginTestCase):
    plugins = ('RatingSystem','User')

    def testRate(self):
        # pre-seed the db with a rating for nanotube
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cb.db.db.commit()
        self.assertError('rate someguy 4') # no cloak
        try:
            #world.testing = False
            self.irc.state.nicksToHostmasks['uncloakedguy'] = 'uncloakedguy!stuff@123.345.5.6'
            self.irc.state.nicksToHostmasks['someguy'] = 'someguy!stuff@stuff/somecloak'
            self.irc.state.nicksToHostmasks['someguy2'] = 'someguy2!stuff@stuff/somecloak'
            self.irc.state.nicksToHostmasks['poorguy'] = 'poorguy!stuff@stuff/somecloak'
            self.irc.state.nicksToHostmasks['SomeDude'] = 'SomeDude!stuff@stuff/somecloak'

            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertError('rate nanotube 10') #can't self-rate
            self.assertError('rate unknownguy 4') #user not in dict
            self.assertError('rate uncloakedguy 6') #user not cloaked
            self.assertRegexp('rate someguy 4', 'rating of 4 for user someguy has been recorded')
            self.assertRegexp('getrating someguy', 'cumulative rating of 4')
            self.assertRegexp('getrating someguy', 'a total of 1')
            self.assertRegexp('rate someguy 6', 'changed from 4 to 6')
            self.assertRegexp('getrating someguy', 'cumulative rating of 6')
            self.assertRegexp('getrating someguy', 'a total of 1')
            self.assertRegexp('getrating nanotube', 'sent 1 positive')
            self.assertError('rate someguy2 0') # rating must be in bounds, and no zeros
            self.assertError('rate someguy2 -20')
            self.assertError('rate someguy2 30')
            self.assertNotError('rate someguy2 -10')
            self.assertRegexp('getrating nanotube', 'sent 1 positive ratings, and 1 negative')
            self.assertRegexp('getrating someguy2', 'cumulative rating of -10')
            self.prefix = 'someguy!stuff@stuff/somecloak'
            self.assertNotError('rate someguy2 9')
            self.assertRegexp('getrating someguy2', 'cumulative rating of -1')
            self.prefix = 'someguy2!stuff@stuff/somecloak'
            self.assertError('rate someguy 2') # rated -1, can't rate
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('unrate someguy2')
            self.assertRegexp('getrating someguy2', 'cumulative rating of 9')
            self.assertNotError('rate poorguy -5')
            self.assertRegexp('getrating nanotube', 'and 1 negative ratings to others')
            self.assertNotError('unrate poorguy')
            self.assertRegexp('getrating nanotube', 'and 0 negative ratings to others')
            self.assertNotError('rate SomeDude 5')
            self.assertNotError('rate somedude 6')
            self.assertRegexp('getrating SomeDude', 'cumulative rating of 6')
            self.assertError('rated nobody')
            self.assertRegexp('rated somedude', 'You rated user somedude .* giving him a rating of 6')
        finally:
            #world.testing = True
            self.prefix = origuser

    def testUnrate(self):
        # pre-seed the db with a rating for nanotube
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cb.db.db.commit()
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertError('unrate someguy') #haven't rated him before
            self.irc.state.nicksToHostmasks['someguy'] = 'someguy!stuff@stuff/somecloak'
            self.assertNotError('rate someguy 4')
            self.assertRegexp('getrating someguy', 'cumulative rating of 4')
            self.assertNotError('unrate somEguy')
            self.assertError('getrating someguy') # guy should be gone, having no connections.
        finally:
            self.prefix = origuser

    def testDeleteUser(self):
        # pre-seed the db with a rating for nanotube
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cb.db.db.commit()
        try:
            self.irc.state.nicksToHostmasks['someguy'] = 'someguy!stuff@stuff/somecloak'
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('rate someguy 4')
            self.assertRegexp('getrating someguy', 'cumulative rating of 4')
            self.assertNotError('deleteuser somEguy')
            self.assertError('getrating someguy') # guy should be gone
        finally:
            self.prefix = origuser


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
