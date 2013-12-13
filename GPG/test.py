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
from supybot import utils

try:
    gnupg = utils.python.universalImport('gnupg', 'local.gnupg')
except ImportError:
    raise callbacks.Error, \
            "You need the gnupg module installed to use this plugin." 

try:
    bitcoinsig = utils.python.universalImport('local.bitcoinsig')
except ImportError:
    raise callbacks.Error, \
            "You are possibly missing the ecdsa module." 


from xmlrpclib import ServerProxy
import shutil
import os, os.path
import time
import ecdsa

class GPGTestCase(PluginTestCase):
    plugins = ('GPG','RatingSystem','Utilities')

    def setUp(self):
        PluginTestCase.setUp(self)
        self.testkeyid = "21E2EF9EF2197A66" # set this to a testing key that we have pregenerated
        self.testkeyfingerprint = "0A969AE0B143927F9D473F3E21E2EF9EF2197A66"
        self.secringlocation = '/tmp/secring.gpg' #where we store our testing secring (normal location gets wiped by test env)
        self.cb = self.irc.getCallback('GPG')
        self.s = ServerProxy('http://paste.debian.net/server.pl')
        shutil.copy(self.secringlocation, self.cb.gpg.gnupghome)
        
        chan = irclib.ChannelState()
        chan.addUser('test')
        chan.addUser('authedguy2')
        self.irc.state.channels['#test'] = chan

        #preseed the GPG db with a GPG registration and auth with some users
        gpg = self.irc.getCallback('GPG')
        gpg.db.register('AAAAAAAAAAAAAAA1', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA1', 'someaddr',
                    time.time(), 'nanotube')
        gpg.authed_users['nanotube!stuff@stuff/somecloak'] = {'nick':'nanotube',
                'keyid':'AAAAAAAAAAAAAAA1', 'fingerprint':'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA1',
                'bitcoinaddress':'1nthoeubla'}
        gpg.db.register('AAAAAAAAAAAAAAA2', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA2', 'someaddr',
                    time.time(), 'registeredguy')
        gpg.db.register('AAAAAAAAAAAAAAA3', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA3', 'someaddr',
                    time.time(), 'authedguy')
        gpg.authed_users['authedguy!stuff@123.345.234.34'] = {'nick':'authedguy',
                'keyid':'AAAAAAAAAAAAAAA3', 'fingerprint':'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA3',
                'bitcoinaddress':'1nthoeubla'}
        gpg.db.register('AAAAAAAAAAAAAAA4', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4', None,
                    time.time(), 'authedguy2')
        gpg.authed_users['authedguy2!stuff@123.345.234.34'] = {'nick':'authedguy2',
                'keyid':'AAAAAAAAAAAAAAA4', 'fingerprint':'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4',
                'bitcoinaddress':None}
        gpg.db.register('AAAAAAAAAAAAAAA5', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA5', 'someaddr',
                    time.time(), 'registered_guy')
        gpg.db.register('AAAAAAAAAAAAAAA6', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA6', 'someaddr',
                    time.time(), 'registe%redguy')

        # create the test ecdsa keypair and resulting bitcoin address
        #~ self.private_key = ecdsa.SigningKey.from_string( '5JkuZ6GLsMWBKcDWa5QiD15Uj467phPR', curve = bitcoinsig.SECP256k1 )
        #~ self.public_key = self.private_key.get_verifying_key()
        #~ self.bitcoinaddress = bitcoinsig.public_key_to_bc_address( '04'.decode('hex') + self.public_key.to_string() )

        #set config to match test environment
        ocn = conf.supybot.plugins.GPG.network()
        conf.supybot.plugins.GPG.network.setValue('test')
        occ = conf.supybot.plugins.GPG.channels()
        conf.supybot.plugins.GPG.channels.setValue('#test')

    def tearDown(self):
        gpg = self.irc.getCallback('GPG')
        gpg.authed_users = {}
        gpg.pending_auth = {}
        PluginTestCase.tearDown(self)

    def testRegister(self):
        # default test user hostmask: test!user@host.domain.tld
        self.assertRegexp('gpg ident', 'not identified')
        self.assertError('register someone 0xBADKEY')
        self.assertError('register someone 0x23420982') # bad length
        self.assertError('register someone 0xAAAABBBBCCCCDDDD') #doesn't exist
        m = self.getMsg('register someone %s' % (self.testkeyid,)) #test without keyserver arg
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1]
        sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
        rc = self.s.paste.addPaste(sd.data, 'gpgtest', 60)
        pasteid = rc['id']
        self.assertRegexp('verify http://paste.debian.net/plain/%s/' % (pasteid,), 
                    'Registration successful. You are now authenticated')

        #are we identified?
        self.assertRegexp('gpg ident', 'is identified')
        self.assertRegexp('gpg ident test', 'is identified')

        #duplicate nick/key registrations
        self.assertError('register someone BBBBBBBBCCCCDDDD') # dupe username
        self.assertError('register newguy %s' % (self.testkeyid,)) #dupe keyid

    def testEregister(self):
        # default test user hostmask: test!user@host.domain.tld
        self.assertRegexp('gpg ident', 'not identified')
        self.assertError('eregister someone 0xBADKEY')
        self.assertError('eregister someone 0x23420982') # bad length
        self.assertError('eregister someone 0xAAAABBBBCCCCDDDD') #doesn't exist
        m = self.getMsg('eregister someone %s' % (self.testkeyid,)) #test without keyserver arg
        self.failUnless('Request successful' in str(m))
        encrypteddata = open(os.path.join(os.getcwd(), 'test-data/otps/%s' % (self.testkeyid,)), 'r').read()
        decrypted = self.cb.gpg.decrypt(encrypteddata)
        self.assertRegexp('everify %s' % (decrypted.data.strip(),), 
                    'Registration successful. You are now authenticated')

        #are we identified?
        self.assertRegexp('gpg ident', 'is identified')
        self.assertRegexp('gpg ident test', 'is identified')

        #duplicate nick/key registrations
        self.assertError('eregister someone BBBBBBBBCCCCDDDD') # dupe username
        self.assertError('eregister newguy %s' % (self.testkeyid,)) #dupe keyid

    def testBcregister(self):
        # create the test ecdsa keypair and resulting bitcoin address
        private_key = ecdsa.SigningKey.from_string( '5JkuZ6GLsMWBKcDWa5QiD15Uj467phPR', curve = bitcoinsig.SECP256k1 )
        public_key = private_key.get_verifying_key()
        bitcoinaddress = bitcoinsig.public_key_to_bc_address( '04'.decode('hex') + public_key.to_string() )
        
        # default test user hostmask: test!user@host.domain.tld
        self.assertRegexp('gpg ident', 'not identified')
        m = self.getMsg('bcregister someone %s' % (bitcoinaddress,))
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1].strip()
        sig = bitcoinsig.sign_message(private_key, challenge)
        time.sleep(1)
        self.assertRegexp('bcverify %s' % (sig,),
                    'Registration successful. You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified')

    def testIdent(self):
        self.prefix = 'authedguy!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        self.assertRegexp('gpg ident authedguy', 'is identified')
        self.assertResponse('echo [gpg ident]', 'authedguy')

    def testStats(self):
        self.assertRegexp('gpg stats', '6 registered users.*3 currently authenticated.*0 pending auth')
        self.assertNotError('gpg auth nanotube')
        self.assertRegexp('gpg stats', '6 registered users.*3 currently authenticated.*1 pending auth')

    def testUnauth(self):
        self.prefix = 'authedguy2!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        self.assertRegexp('gpg unauth', 'has been terminated')
        self.assertRegexp('gpg ident', 'not identified')

    def testAuth(self):
        self.assertNotError('gpg register bla %s' % (self.testkeyid,)) # just to get the pubkey into the keyring
        gpg = self.irc.getCallback('GPG')
        gpg.db.register(self.testkeyid, self.testkeyfingerprint,'1somebitcoinaddress',
                    time.time(), 'someone')
        m = self.getMsg('auth someone')
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1]
        sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
        rc = self.s.paste.addPaste(sd.data, 'gpgtest', 60)
        pasteid = rc['id']
        self.assertRegexp('verify http://paste.debian.net/plain/%s/' % (pasteid,),
                    'You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified')

    def testEauth(self):
        self.assertNotError('gpg register bla %s' % (self.testkeyid,)) # just to get the pubkey into the keyring
        gpg = self.irc.getCallback('GPG')
        gpg.db.register(self.testkeyid, self.testkeyfingerprint, 'someaddr',
                    time.time(), 'someone')
        self.assertNotError('eauth someone')
        m = self.getMsg('eauth someone')
        self.failUnless('Request successful' in str(m))
        encrypteddata = open(os.path.join(os.getcwd(), 'test-data/otps/%s' % (self.testkeyid,)), 'r').read()
        decrypted = self.cb.gpg.decrypt(encrypteddata)
        self.assertRegexp('everify %s' % (decrypted.data.strip(),), 'You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified')

    def testBcauth(self):
        # create the test ecdsa keypair and resulting bitcoin address
        private_key = ecdsa.SigningKey.from_string( '5JkuZ6GLsMWBKcDWa5QiD15Uj467phPR', curve = bitcoinsig.SECP256k1 )
        public_key = private_key.get_verifying_key()
        bitcoinaddress = bitcoinsig.public_key_to_bc_address( '04'.decode('hex') + public_key.to_string() )
        
        gpg = self.irc.getCallback('GPG')
        gpg.db.register(self.testkeyid, self.testkeyfingerprint, bitcoinaddress,
                    time.time(), 'someone')
        m = self.getMsg('bcauth someone')
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1].strip()
        sig = bitcoinsig.sign_message(private_key, challenge)
        time.sleep(1)
        self.assertRegexp('bcverify %s' % (sig,), 'You are now authenticated')

    #~ def testChangenick(self):
        #~ self.assertError('gpg changenick somethingnew') #not authed
        #~ self.prefix = 'authedguy2!stuff@123.345.234.34'
        #~ self.assertRegexp('gpg ident', 'is identified')
        #~ self.assertRegexp('gpg changenick mycoolnewnick',
                #~ 'changed your nick from authedguy2 to mycoolnewnick')
        #~ self.assertRegexp('gpg ident authedguy2', 'identified as user mycoolnewnick')
        #~ self.assertRegexp('gpg info mycoolnewnick', "User 'mycoolnewnick'.* registered on")

    def testChangekey(self):
        self.assertError('gpg changekey AAAAAAAAAAAAAAA1') #not authed
        self.prefix = 'authedguy2!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        m = self.getMsg('gpg changekey %s' % (self.testkeyid,))
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1]
        sd = self.cb.gpg.sign(challenge, keyid = self.testkeyid)
        rc = self.s.paste.addPaste(sd.data, 'gpgtest', 60)
        pasteid = rc['id']
        self.assertRegexp('verify http://paste.debian.net/plain/%s/' % (pasteid,),
                    'Successfully changed key.*You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified.*key id %s' % (self.testkeyid,))

    def testEchangekey(self):
        self.assertError('gpg echangekey AAAAAAAAAAAAAAA1') #not authed
        self.prefix = 'authedguy2!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        m = self.getMsg('gpg echangekey %s' % (self.testkeyid,))
        self.failUnless('Request successful' in str(m))
        encrypteddata = open(os.path.join(os.getcwd(), 'test-data/otps/%s' % (self.testkeyid,)), 'r').read()
        decrypted = self.cb.gpg.decrypt(encrypteddata)
        self.assertRegexp('everify %s' % (decrypted.data.strip(),),
                    'Successfully changed key.*You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified.*key id %s' % (self.testkeyid,))

    def testChangeaddress(self):
        # create the test ecdsa keypair and resulting bitcoin address
        private_key = ecdsa.SigningKey.from_string( '5JkuZ6GLsMWBKcDWa5QiD15Uj467phPR', curve = bitcoinsig.SECP256k1 )
        public_key = private_key.get_verifying_key()
        bitcoinaddress = bitcoinsig.public_key_to_bc_address( '04'.decode('hex') + public_key.to_string() )

        self.assertError('gpg changeaddress 1sntoheu') #not authed
        self.prefix = 'authedguy2!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        m = self.getMsg('gpg changeaddress %s' % (bitcoinaddress,))
        self.failUnless('Request successful' in str(m))
        challenge = str(m).split('is: ')[1].strip()
        sig = bitcoinsig.sign_message(private_key, challenge)
        time.sleep(1)
        self.assertRegexp('bcverify %s' % (sig,),
                    'Successfully changed address.*You are now authenticated')
        self.assertRegexp('gpg ident', 'is identified.*address %s' % (bitcoinaddress,))
        self.assertRegexp('gpg info authedguy2', 'address %s' % (bitcoinaddress,))

    def testNick(self):
        self.prefix = 'authedguy2!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        self.irc.feedMsg(msg=ircmsgs.nick('newnick', prefix=self.prefix))
        self.assertRegexp('gpg ident', 'not identified')
        self.prefix = 'newnick' + '!' + self.prefix.split('!',1)[1]
        self.assertRegexp('gpg ident', 'is identified')

    def testOuit(self):
        self.prefix = 'authedguy!stuff@123.345.234.34'
        self.irc.feedMsg(msg=ircmsgs.quit(prefix=self.prefix))
        self.assertRegexp('gpg ident', 'not identified')
        chan = irclib.ChannelState()

    def testPart(self):
        self.prefix = 'authedguy!stuff@123.345.234.34'
        self.assertRegexp('gpg ident', 'is identified')
        self.irc.feedMsg(msg=ircmsgs.part("#test", prefix=self.prefix))
        self.assertRegexp('gpg ident', 'not identified')

    def testKick(self):
        # do it as the stock test user, because he has admin capability and can kick
        gpg = self.irc.getCallback('GPG')
        gpg.authed_users['test!user@host.domain.tld'] = {'nick':'test',
                'keyid':'AAAAAAAAAAAAAAA4', 'fingerprint':'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4',
                'bitcoinaddress':'1blabsanthoeu'}
        self.prefix = 'test!user@host.domain.tld' 
        self.assertRegexp('gpg ident', 'is identified')
        self.irc.feedMsg(msg=ircmsgs.kick("#test", 'test', prefix=self.prefix))
        self.assertRegexp('gpg ident', 'not identified')

    def testInfo(self):
        self.assertRegexp('gpg info registeredguy', "User 'registeredguy'.*registered on.*Currently not authenticated")
        self.assertRegexp('gpg info authedguy', "User 'authedguy'.*registered on.*Currently authenticated")
        self.assertRegexp('gpg info authEDguY', "User 'authedguy'.*registered on.*Currently authenticated")
        self.assertRegexp('gpg info AAAAAAAAAAAAAAA1', "No such user registered")
        self.assertRegexp('gpg info --key AAAAAAAAAAAAAAA1', "User 'nanotube'.*registered on")
        self.assertRegexp('gpg info authedgu_', "No such user registered")
        self.assertRegexp('gpg info authed%', "No such user registered")
        self.assertRegexp('gpg info registered_guy', "User 'registered_guy'")
        self.assertRegexp('gpg info registe%redguy', "User 'registe%redguy'")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
