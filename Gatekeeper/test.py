###
# Copyright (c) 2011, Daniel Folkinshteyn
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
from supybot import ircmsgs

class GatekeeperTestCase(PluginTestCase):
    plugins = ('Gatekeeper','RatingSystem','GPG','Admin')
    
    def setUp(self):
        PluginTestCase.setUp(self)

        #preseed the GPG db with a GPG registration and auth for nanotube
        gpg = self.irc.getCallback('GPG')
        gpg.db.register('AAAAAAAAAAAAAAA1', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA1',
                    '1somebitcoinaddress', time.time() - 1000000, 'nanotube')
        gpg.authed_users['nanotube!stuff@stuff/somecloak'] = {'nick':'nanotube'}
        gpg.db.register('AAAAAAAAAAAAAAA2', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA2',
                    '1somebitcoinaddress', time.time(), 'registeredguy')
        gpg.db.register('AAAAAAAAAAAAAAA7', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA7',
                    '1somebitcoinaddress', time.time(), 'youngguy')
        gpg.authed_users['youngguy!stuff@123.345.234.34'] = {'nick':'youngguy'}
        gpg.db.register('AAAAAAAAAAAAAAA3', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA3',
                    '1somebitcoinaddress', time.time() - 1000000, 'authedguy')
        gpg.authed_users['authedguy!stuff@123.345.234.34'] = {'nick':'authedguy'}
        gpg.db.register('AAAAAAAAAAAAAAA4', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4',
                    '1somebitcoinaddress', time.time() - 1000000, 'authedguy2')
        gpg.authed_users['authedguy2!stuff@123.345.234.34'] = {'nick':'authedguy2'}

        # pre-seed the rating db with some ratings
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'Keefe','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'authedguy','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (-10, time.time(), 1, 0, 0, 0, 'authedguy2','stuff/somecloak'))
        cursor.execute("""INSERT INTO ratings VALUES
                        (NULL, ?, ?, ?, ?, ?)""",
                        (3, 1, time.time(), 1, "some notes",)) # nanotube rates authedguy
        cursor.execute("""INSERT INTO ratings VALUES
                        (NULL, ?, ?, ?, ?, ?)""",
                        (2, 1, time.time(), 9, "some notes",)) # nanotube rates keefe
        cursor.execute("""INSERT INTO ratings VALUES
                        (NULL, ?, ?, ?, ?, ?)""",
                        (3, 2, time.time(), 2, "some notes",)) # keefe rates authedguy
        cursor.execute("""INSERT INTO ratings VALUES
                        (NULL, ?, ?, ?, ?, ?)""",
                        (4, 2, time.time(), -5, "some notes",)) # keefe rates authedguy2

        cb.db.db.commit()

    def testLetmein(self):
        def getAfterJoinMessages():
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'MODE')
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'WHO')
        self.irc.feedMsg(ircmsgs.join('#bitcoin-otc', prefix=self.prefix))
        getAfterJoinMessages()
        try:
            orignetwork = self.irc.network
            self.irc.network = 'freenode'
            origuser = self.prefix
            self.prefix = 'registeredguy!stuff@123.345.234.34'
            self.assertError('letmein') # not authed
            self.irc.feedMsg(ircmsgs.join('#bitcoin-otc', prefix=self.prefix))
            self.irc.takeMsg()
            self.assertTrue('registeredguy' not in self.irc.state.channels['#bitcoin-otc'].voices)
            self.prefix = 'youngguy!stuff@123.345.234.34'
            self.assertError('letmein') # not enough account age
            self.irc.feedMsg(ircmsgs.join('#bitcoin-otc', prefix=self.prefix))
            self.irc.takeMsg()
            self.assertTrue('youngguy' not in self.irc.state.channels['#bitcoin-otc'].voices)
            self.prefix = 'authedguy2!stuff@123.345.234.34'
            self.assertError('letmein') # negative rating
            self.irc.feedMsg(ircmsgs.join('#bitcoin-otc', prefix=self.prefix))
            self.irc.takeMsg()
            self.assertTrue('authedguy2' not in self.irc.state.channels['#bitcoin-otc'].voices)
            self.prefix = 'authedguy!stuff@123.345.234.34'
            self.assertNotError('letmein') # should be good
            self.irc.feedMsg(ircmsgs.join('#bitcoin-otc', prefix=self.prefix))
            self.irc.takeMsg()
            self.assertTrue('authedguy' in self.irc.state.channels['#bitcoin-otc'].voices)
        finally:
            self.irc.network = orignetwork
            self.prefix = origuser


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
