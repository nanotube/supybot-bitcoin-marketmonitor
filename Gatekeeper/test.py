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

class GatekeeperTestCase(PluginTestCase):
    plugins = ('Gatekeeper','RatingSystem','GPG')
    
    def setUp(self):
        PluginTestCase.setUp(self)

        #preseed the GPG db with a GPG registration and auth for nanotube
        gpg = self.irc.getCallback('GPG')
        gpg.db.register('AAAAAAAAAAAAAAA1', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA1',
                    time.time() - 1000000, 'nanotube')
        gpg.authed_users['nanotube!stuff@stuff/somecloak'] = {'nick':'nanotube'}
        gpg.db.register('AAAAAAAAAAAAAAA2', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA2',
                    time.time(), 'registeredguy')
        gpg.db.register('AAAAAAAAAAAAAAA3', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA3',
                    time.time(), 'authedguy')
        gpg.authed_users['authedguy!stuff@123.345.234.34'] = {'nick':'authedguy'}
        gpg.db.register('AAAAAAAAAAAAAAA4', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4',
                    time.time() - 1000000, 'authedguy2')
        gpg.authed_users['authedguy2!stuff@123.345.234.34'] = {'nick':'authedguy2'}

        # pre-seed the rating db with some ratings, for testing long orders
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'authedguy','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (-10, time.time(), 1, 0, 0, 0, 'authedguy2','stuff/somecloak'))
        cb.db.db.commit()

    def testLetmein(self):
        self.assertError('letmein') # not authed
        try:
            origuser = self.prefix
            self.prefix = 'authedguy!stuff@123.345.234.34'
            self.assertError('letmein') # not enough account age
            self.prefix = 'authedguy2!stuff@123.345.234.34'
            self.assertError('letmein') # negative rating
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('letmein') # should be good.
        finally:
            self.prefix = origuser


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
