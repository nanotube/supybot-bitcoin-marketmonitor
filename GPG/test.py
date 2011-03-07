###
# GPG - supybot plugin to authenticate users via GPG keys
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
from supybot import ircmsgs
from supybot import conf
from supybot import irclib

try:
    gnupg = utils.python.universalImport('gnupg', 'local.gnupg')
except ImportError:
    raise callbacks.Error, \
            "You need the gnupg module installed to use this plugin." 

from xmlrpclib import ServerProxy
import shutil

class GPGTestCase(PluginTestCase):
    plugins = ('GPG',)

    def setUp(self):
        PluginTestCase.setUp(self)
        self.testkeyid = "21E2EF9EF2197A66" # set this to a testing key that we have pregenerated
        self.secringlocation = '/tmp/secring.gpg' #where we store our testing secring (normal location gets wiped by test env)
        self.cb = self.irc.getCallback('GPG')
        self.s = ServerProxy('http://paste.pocoo.org/xmlrpc/')
        shutil.copy(self.secringlocation, self.cb.gpg.gnupghome)
        
        chan = irclib.ChannelState()
        chan.addUser('test')
        self.irc.state.channels['#test'] = chan

    def testRegister(self):
        try:
            ocn = conf.supybot.plugins.GPG.network()
            conf.supybot.plugins.GPG.network.setValue('test')
            occ = conf.supybot.plugins.GPG.channels()
            conf.supybot.plugins.GPG.channels.setValue('#test')

            #test register
            self.assertRegexp('gpg ident', 'not identified')
            self.assertError('register someone 0xBADKEY')
            self.assertError('register someone 0x23420982') # bad length
            self.assertError('register someone 0xAAAABBBBCCCCDDDD') #doesn't exist
            self.cb.gpg.list_keys()
            m = self.getMsg('register someone %s' % (self.testkeyid,))
            self.failUnless('Request successful' in str(m))
            challenge = str(m).split('is: ')[1]
            sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
            pasteid = self.s.pastes.newPaste('text',sd.data)
            self.assertRegexp('verify http://paste.pocoo.org/raw/%s/' % (pasteid,), 
                        'Registration successful. You are now authenticated')

            #test ident
            self.assertRegexp('gpg ident', 'You are identified')
            self.assertRegexp('gpg ident test', 'is identified')

            #test unauth
            self.assertRegexp('gpg unauth', 'has been terminated')
            self.assertRegexp('gpg ident', 'not identified')

            #duplicate nick/key registrations
            self.assertError('register someone BBBBBBBBCCCCDDDD')
            self.assertError('register newguy %s' % (self.testkeyid,))

            #test auth
            m = self.getMsg('auth someone')
            self.failUnless('Request successful' in str(m))
            challenge = str(m).split('is: ')[1]
            sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
            pasteid = self.s.pastes.newPaste('text',sd.data)
            self.assertRegexp('verify http://paste.pocoo.org/raw/%s/' % (pasteid,), 
                        'You are now authenticated')
            self.assertRegexp('gpg ident', 'You are identified')

            #test nick
            op = self.prefix
            self.irc.feedMsg(msg=ircmsgs.nick('newnick', prefix=self.prefix))
            self.assertRegexp('gpg ident', 'not identified')
            self.prefix = 'newnick' + '!' + self.prefix.split('!',1)[1]
            self.assertRegexp('gpg ident', 'You are identified')
            self.irc.feedMsg(msg=ircmsgs.nick('test', prefix=self.prefix))
            self.prefix = op

            #test quit
            self.irc.feedMsg(msg=ircmsgs.quit(prefix=self.prefix))
            self.assertRegexp('gpg ident', 'not identified')
            chan = irclib.ChannelState()
            chan.addUser('test')
            self.irc.state.channels['#test'] = chan

            m = self.getMsg('auth someone')
            self.failUnless('Request successful' in str(m))
            challenge = str(m).split('is: ')[1]
            sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
            pasteid = self.s.pastes.newPaste('text',sd.data)
            self.assertRegexp('verify http://paste.pocoo.org/raw/%s/' % (pasteid,), 
                        'You are now authenticated')
            self.assertRegexp('gpg ident', 'You are identified')

            #test part
            self.irc.feedMsg(msg=ircmsgs.part("#test", prefix=self.prefix))
            self.assertRegexp('gpg ident', 'not identified')
            chan = irclib.ChannelState()
            chan.addUser('test')
            self.irc.state.channels['#test'] = chan

            m = self.getMsg('auth someone')
            self.failUnless('Request successful' in str(m))
            challenge = str(m).split('is: ')[1]
            sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
            pasteid = self.s.pastes.newPaste('text',sd.data)
            self.assertRegexp('verify http://paste.pocoo.org/raw/%s/' % (pasteid,), 
                        'You are now authenticated')
            self.assertRegexp('gpg ident', 'You are identified')

            #test kick
            self.irc.feedMsg(msg=ircmsgs.kick("#test", 'test', prefix=self.prefix))
            self.assertRegexp('gpg ident', 'not identified')
        finally:
            conf.supybot.plugins.GPG.network.setValue(ocn)
            conf.supybot.plugins.GPG.channels.setValue(occ)

        #test info
        self.assertRegexp('gpg info someone', "User 'someone'.*registered on")
        self.assertRegexp('gpg info somEoNe', "User 'someone'.*registered on")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
