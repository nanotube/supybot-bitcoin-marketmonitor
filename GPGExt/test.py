###
# GPGExt - supybot plugin to verify user identity on external sites using GPG keys
# Copyright (C) 2011, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###

from supybot.test import *

class GPGExtTestCase(PluginTestCase):
    plugins = ('GPGExt','GPG')

    def setUp(self):
        PluginTestCase.setUp(self)

        #preseed the GPG db with a GPG registration and auth for mndrix
        gpg = self.irc.getCallback('GPG')
        gpg.db.register('CE52C98A48081991', '60E2810AB29BE577E40EF118CE52C98A48081991',
                    time.time(), 'mndrix')
        gpg.authed_users['mndrix!stuff@stuff/somecloak'] = {'nick':'mndrix'}
        gpg.gpg.recv_keys('pgp.mit.edu', 'CE52C98A48081991')
        gpg.db.register('E7F938BEC95594B2', 'D8B11AAC59A873B0F38D475CE7F938BEC95594B2',
                    time.time(), 'nanotube')
        gpg.gpg.recv_keys('pgp.mit.edu', 'E7F938BEC95594B2')

    def testVerify(self):
        self.assertRegexp('GPGExt verify http://myworld.ebay.com/mndrix mndrix', 'Verified signature')
        self.prefix =  'mndrix!stuff@stuff/somecloak'
        self.assertRegexp('GPGExt verify http://www.bitcoin.org/smf/index.php?action=profile;u=2538', 'Verified signature')
        self.assertError('GPGExt verify badurl') # bad url
        self.assertError('GPGExt verify http://google.com') #no tag
        self.assertError('GPGExt verify http://google.com nosuchuser') #bad user
        self.assertRegexp('GPGExt verify http://nanotube.users.sourceforge.net nanotube', 'Verified signature')

    def testEbay(self):
        self.assertRegexp('GPGExt ebay mndrix mndrix', 'Verified signature')
        self.assertError('GPGExt ebay mndrix nanotube')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
