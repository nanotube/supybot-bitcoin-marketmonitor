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

from supybot import conf
from supybot import ircmsgs
from supybot import world
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.log

import sqlite3
import re
import os
import os.path
import errno
import hashlib
import time
import copy
import logging
import traceback

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


domainRe = re.compile('^' + utils.web._domain + '$', re.I)
urlRe = re.compile('^' + utils.web._urlRe + '$', re.I)

class GPGDB(object):
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
            db = sqlite3.connect(self.filename, timeout=10, check_same_thread = False)
            db.text_factory = str
            self.db = db
            return
        
        db = sqlite3.connect(self.filename, timeout=10, check_same_thread = False)
        db.text_factory = str
        self.db = db
        cursor = self.db.cursor()
        cursor.execute("""CREATE TABLE users (
                          id INTEGER PRIMARY KEY,
                          keyid TEXT,
                          fingerprint TEXT,
                          bitcoinaddress TEXT,
                          registered_at INTEGER,
                          nick TEXT)
                           """)
        self._commit()
        return

    def close(self):
        self.db.close()

    def getByNick(self, nick):
        cursor = self.db.cursor()
        nick = nick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor.execute("""SELECT * FROM users WHERE nick LIKE ? ESCAPE '|'""", (nick,))
        return cursor.fetchall()

    def getByKey(self, keyid):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM users WHERE keyid = ?""", (keyid,))
        return cursor.fetchall()

    def getByAddr(self, address):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM users WHERE bitcoinaddress = ?""", (address,))
        return cursor.fetchall()

    def getCount(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT count(*) FROM users""")
        return cursor.fetchall()

    def register(self, keyid, fingerprint, bitcoinaddress, timestamp, nick):
        cursor = self.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                        (NULL, ?, ?, ?, ?, ?)""",
                        (keyid, fingerprint, bitcoinaddress, timestamp, nick))
        self._commit()

    def changenick(self, oldnick, newnick):
        cursor = self.db.cursor()
        cursor.execute("""UPDATE users SET nick = ? WHERE nick = ?""",
                        (newnick, oldnick,))
        self._commit()

    def changekey(self, nick, oldkeyid, newkeyid, newkeyfingerprint):
        cursor = self.db.cursor()
        cursor.execute("""UPDATE users SET keyid = ?, fingerprint = ?
                        WHERE (keyid = ? OR keyid IS NULL) and nick = ?""",
                        (newkeyid, newkeyfingerprint, oldkeyid, nick))
        self._commit()

    def changeaddress(self, nick, oldaddress, newaddress):
        cursor = self.db.cursor()
        cursor.execute("""UPDATE users SET bitcoinaddress = ?
                        WHERE nick = ? AND (bitcoinaddress = ? OR bitcoinaddress IS NULL)""",
                        (newaddress, nick, oldaddress,))
        self._commit()

def getGPGKeyID(irc, msg, args, state, type='GPG key id. Please use the long form 16 digit key id'):
    v = args[0]
    m = re.search(r'^(0x)?([0-9A-Fa-f]{16})$', v)
    if m is None:
        state.errorInvalid(type, args[0])
        return
    state.args.append(m.group(2).upper())
    del args[0]

def getUsername(irc, msg, args, state, type='username. Usernames must contain only printable ASCII characters with no whitespace'):
    v = args[0]
    m = re.search(r"^[!-~]+$", v)
    if m is None:
        state.errorInvalid(type, args[0])
        return
    state.args.append(m.group(0))
    del args[0]

addConverter('keyid', getGPGKeyID)
addConverter('username', getUsername)

class GPG(callbacks.Plugin):
    """This plugin lets users create identities based on GPG keys,
    and to authenticate via GPG signed messages."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(GPG, self)
        self.__parent.__init__(irc)
        self.filename = conf.supybot.directories.data.dirize('GPG.db')
        self.db = GPGDB(self.filename)
        self.db.open()
        try:
            os.makedirs(conf.supybot.directories.data.dirize('otps'))
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
        self.gpg = gnupg.GPG(gnupghome = conf.supybot.directories.data.dirize('GPGkeyring'))
        try: #restore auth dicts, if we're reloading the plugin
            self.authed_users = utils.gpg_authed_users
            utils.gpg_authed_users = {}
            self.pending_auth = utils.gpg_pending_auth
            utils.gpg_pending_auth = {}
        except AttributeError:
            self.pending_auth = {}
            self.authed_users = {}
        authlogfilename = os.path.join(conf.supybot.directories.log(), 'gpgauthlog.log')
        authlog = logging.getLogger('GPGauth')
        authlog.setLevel(-1)
        if len(authlog.handlers) == 0:
            handler = supybot.log.BetterFileHandler(authlogfilename)
            handler.setLevel(-1)
            handler.setFormatter(supybot.log.pluginFormatter)
            authlog.addHandler(handler)
        self.authlog = authlog
        self.authlog.info("***** loading GPG plugin. *****")

    def die(self):
        self.__parent.die()
        self.db.close()
        # save auth dicts, in case we're reloading the plugin
        utils.gpg_authed_users = self.authed_users
        utils.gpg_pending_auth = self.pending_auth
        self.authlog.info("***** quitting or unloading GPG plugin. *****")

    def _recv_key(self, keyservers, keyid):
        for ks in keyservers:
            try:
                result = self.gpg.recv_keys(ks, keyid)
                if result.results[0].has_key('ok'):
                    return result.results[0]['fingerprint']
            except:
               continue
        else:
            raise Exception(result.stderr)

    def _removeExpiredRequests(self):
        pending_auth_copy = copy.deepcopy(self.pending_auth)
        for hostmask,auth in pending_auth_copy.iteritems():
            try:
                if time.time() - auth['expiry'] > self.registryValue('authRequestTimeout'):
                    if auth['type'] == 'register' and not self.db.getByKey(auth['keyid']):
                        try:
                            self.gpg.delete_keys(auth['fingerprint'])
                        except:
                            pass
                    del self.pending_auth[hostmask]
            except:
                pass #let's keep going

    def _checkURLWhitelist(self, url):
        if not self.registryValue('pastebinWhitelist'):
            return True
        passed = False
        for wu in self.registryValue('pastebinWhitelist'):
            if wu.endswith('/') and url.find(wu) == 0:
                passed = True
                break
            if (not wu.endswith('/')) and (url.find(wu + '/') == 0):
                passed = True
                break
        return passed

    def register(self, irc, msg, args, nick, keyid):
        """<nick> <keyid>

        Register your GPG identity, associating GPG key <keyid> with <nick>.
        <keyid> is a 16 digit key id, with or without the '0x' prefix.
        We look on servers listed in 'plugins.GPG.keyservers' config.
        You will be given a random passphrase to clearsign with your key, and
        submit to the bot with the 'verify' command.
        Your passphrase will expire in 10 minutes.
        """
        self._removeExpiredRequests()
        if self.db.getByNick(nick):
            irc.error("Username already registered. Try a different username.")
            return
        if self.db.getByKey(keyid):
            irc.error("This key already registered in the database.")
            return
        rs = irc.getCallback('RatingSystem')
        rsdata = rs.db.get(nick)
        if len(rsdata) != 0:
            irc.error("This username is reserved for a legacy user. "
                    "Contact otc administrator to reclaim the account, if "
                    "you are an oldtimer since before key auth.")
            return
        keyservers = self.registryValue('keyservers').split(',')
        try:
            fingerprint = self._recv_key(keyservers, keyid)
        except Exception as e:
            irc.error("Could not retrieve your key from keyserver. "
                    "Either it isn't there, or it is invalid.")
            self.log.info("GPG register: failed to retrieve key %s from keyservers %s. Details: %s" % \
                    (keyid, keyservers, e,))
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'keyid':keyid,
                            'nick':nick, 'expiry':time.time(),
                            'type':'register', 'fingerprint':fingerprint,
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("register request from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, nick, keyid, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (nick, msg.prefix, challenge,))
    register = wrap(register, ['username', 'keyid'])

    def eregister(self, irc, msg, args, nick, keyid):
        """<nick> <keyid>

        Register your GPG identity, associating GPG key <keyid> with <nick>.
        <keyid> is a 16 digit key id, with or without the '0x' prefix.
        We look on servers listed in 'plugins.GPG.keyservers' config.
        You will be given a link to a page which contains a one time password
        encrypted with your key. Decrypt, and use the 'everify' command with it.
        Your passphrase will expire in 10 minutes.
        """
        self._removeExpiredRequests()
        if self.db.getByNick(nick):
            irc.error("Username already registered. Try a different username.")
            return
        if self.db.getByKey(keyid):
            irc.error("This key already registered in the database.")
            return
        rs = irc.getCallback('RatingSystem')
        rsdata = rs.db.get(nick)
        if len(rsdata) != 0:
            irc.error("This username is reserved for a legacy user. "
                    "Contact otc administrator to reclaim the account, if "
                    "you are an oldtimer since before key auth.")
            return
        keyservers = self.registryValue('keyservers').split(',')
        try:
            fingerprint = self._recv_key(keyservers, keyid)
        except Exception as e:
            irc.error("Could not retrieve your key from keyserver. "
                    "Either it isn't there, or it is invalid.")
            self.log.info("GPG eregister: failed to retrieve key %s from keyservers %s. Details: %s" % \
                    (keyid, keyservers, e,))
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        try:
            data = self.gpg.encrypt(challenge + '\n', keyid, always_trust=True)
            if data.status != "encryption ok":
                raise ValueError, "problem encrypting otp"
            otpfn = conf.supybot.directories.data.dirize('otps/%s' % (keyid,))
            f = open(otpfn, 'w')
            f.write(data.data)
            f.close()
        except Exception, e:
            irc.error("Problem creating encrypted OTP file.")
            self.log.info("GPG eregister: key %s, otp creation %s, exception %s" % \
                    (keyid, data.stderr, e,))
            return
        request = {msg.prefix: {'keyid':keyid,
                            'nick':nick, 'expiry':time.time(),
                            'type':'eregister', 'fingerprint':fingerprint,
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("eregister request from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, nick, keyid,))
        irc.reply("Request successful for user %s, hostmask %s. Get your encrypted OTP from %s" %\
                (nick, msg.prefix, 'http://bitcoin-otc.com/otps/%s' % (keyid,),))
    eregister = wrap(eregister, ['username', 'keyid'])

    def bcregister(self, irc, msg, args, nick, bitcoinaddress):
        """<nick> <bitcoinaddress>

        Register your identity, associating bitcoin address key <bitcoinaddress>
        with <nick>.
        <bitcoinaddress> should be a standard-type bitcoin address, starting with 1.
        You will be given a random passphrase to sign with your address key, and
        submit to the bot with the 'bcverify' command.
        Your passphrase will expire in 10 minutes.
        """
        self._removeExpiredRequests()
        if self.db.getByNick(nick):
            irc.error("Username already registered. Try a different username.")
            return
        if self.db.getByAddr(bitcoinaddress):
            irc.error("This address is already registered in the database.")
            return
        rs = irc.getCallback('RatingSystem')
        rsdata = rs.db.get(nick)
        if len(rsdata) != 0:
            irc.error("This username is reserved for a legacy user. "
                    "Contact otc administrator to reclaim the account, if "
                    "you are an oldtimer since before key auth.")
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'bitcoinaddress':bitcoinaddress,
                            'nick':nick, 'expiry':time.time(),
                            'type':'bcregister',
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("bcregister request from hostmask %s for user %s, bitcoinaddress %s." %\
                (msg.prefix, nick, bitcoinaddress, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (nick, msg.prefix, challenge,))
    bcregister = wrap(bcregister, ['username', 'something'])

    def auth(self, irc, msg, args, nick):
        """<nick>

        Initiate authentication for user <nick>.
        You must have registered a GPG key with the bot for this to work.
        You will be given a random passphrase to clearsign with your key, and
        submit to the bot with the 'verify' command.
        Your passphrase will expire within 10 minutes.
        """
        self._removeExpiredRequests()
        userdata = self.db.getByNick(nick)
        if len(userdata) == 0:
            irc.error("This nick is not registered. Please register.")
            return
        keyid = userdata[0][1]
        fingerprint = userdata[0][2]
        if keyid is None:
            irc.error("You have not registered a GPG key. Try using bcauth instead, or register a GPG key first.")
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'nick':userdata[0][5],
                                'expiry':time.time(), 'keyid':keyid,
                                'type':'auth', 'challenge':challenge,
                                'fingerprint':fingerprint}}
        self.pending_auth.update(request)
        self.authlog.info("auth request from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, nick, keyid, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (nick, msg.prefix, challenge,))
    auth = wrap(auth, ['username'])

    def eauth(self, irc, msg, args, nick):
        """<nick>

        Initiate authentication for user <nick>.
        You must have registered a GPG key with the bot for this to work.
        You will be given a link to a page which contains a one time password
        encrypted with your key. Decrypt, and use the 'everify' command with it.
        Your passphrase will expire in 10 minutes.
        """
        self._removeExpiredRequests()
        userdata = self.db.getByNick(nick)
        if len(userdata) == 0:
            irc.error("This nick is not registered. Please register.")
            return
        keyid = userdata[0][1]
        fingerprint = userdata[0][2]
        if keyid is None:
            irc.error("You have not registered a GPG key. Try using bcauth instead, or register a GPG key first.")
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        try:
            data = None
            data = self.gpg.encrypt(challenge + '\n', keyid, always_trust=True)
            if data.status != "encryption ok":
                raise ValueError, "problem encrypting otp"
            otpfn = conf.supybot.directories.data.dirize('otps/%s' % (keyid,))
            f = open(otpfn, 'w')
            f.write(data.data)
            f.close()
        except Exception, e:
            irc.error("Problem creating encrypted OTP file.")
            if 'stderr' in dir(data):
                gpgerroroutput = data.stderr
            else:
                gpgerroroutput = None
            self.log.info("GPG eauth: key %s, otp creation %s, exception %s" % \
                    (keyid, gpgerroroutput, e,))
            return
        request = {msg.prefix: {'nick':userdata[0][5],
                                'expiry':time.time(), 'keyid':keyid,
                                'type':'eauth', 'challenge':challenge,
                                'fingerprint':fingerprint}}
        self.pending_auth.update(request)
        self.authlog.info("eauth request from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, nick, keyid, ))
        irc.reply("Request successful for user %s, hostmask %s. Get your encrypted OTP from %s" %\
                (nick, msg.prefix, 'http://bitcoin-otc.com/otps/%s' % (keyid,),))
    eauth = wrap(eauth, ['username'])

    def bcauth(self, irc, msg, args, nick):
        """<nick>

        Initiate authentication for user <nick>.
        You must have registered with the bot with a bitcoin address for this to work.
        You will be given a random passphrase to sign with your address, and
        submit to the bot with the 'bcverify' command.
        Your passphrase will expire within 10 minutes.
        """
        self._removeExpiredRequests()
        userdata = self.db.getByNick(nick)
        if len(userdata) == 0:
            irc.error("This nick is not registered. Please register.")
            return
        bitcoinaddress = userdata[0][3]
        if bitcoinaddress is None:
            irc.error("You have not registered a bitcoin address. Try using auth/eauth instead, or register an address first.")
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'nick':userdata[0][5],
                                'expiry':time.time(),
                                'type':'bcauth', 'challenge':challenge,
                                'bitcoinaddress':bitcoinaddress}}
        self.pending_auth.update(request)
        self.authlog.info("bcauth request from hostmask %s for user %s, bitcoinaddress %s." %\
                (msg.prefix, nick, bitcoinaddress, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (nick, msg.prefix, challenge,))
    bcauth = wrap(bcauth, ['username'])

    def _unauth(self, irc, hostmask):
        try:
            logmsg = "Terminating session for hostmask %s, authenticated to user %s, keyid %s, bitcoinaddress %s" % (hostmask, self.authed_users[hostmask]['nick'], self.authed_users[hostmask]['keyid'],self.authed_users[hostmask]['bitcoinaddress'],)
            self.authlog.info(logmsg)
            del self.authed_users[hostmask]
            if not world.testing:
                irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-auth", logmsg))
            return True
        except KeyError:
            return False

    def unauth(self, irc, msg, args):
        """takes no arguments
        
        Unauthenticate, 'logout' of your GPG session.
        """
        if self._unauth(irc, msg.prefix):
            irc.reply("Your GPG session has been terminated.")
        else:
            irc.error("You do not have a GPG session to terminate.")
    unauth = wrap(unauth)

    def _testPresenceInChannels(self, irc, nick):
        """Make sure authenticating user is present in channels being monitored."""
        for channel in self.registryValue('channels').split(';'):
            try:
                if nick in irc.state.channels[channel].users:
                    return True
            except KeyError:
                pass
        else:
            return False

    def verify(self, irc, msg, args, url):
        """<url>

        Verify the latest authentication request by providing a pastebin <url>
        which contains the challenge string clearsigned with your GPG key
        of record. If verified, you'll be authenticated for the duration of the bot's
        or your IRC session on channel (whichever is shorter).
        """
        self._removeExpiredRequests()
        if not self._checkURLWhitelist(url):
            irc.error("Only these pastebins are supported: %s" % \
                    self.registryValue('pastebinWhitelist'))
            return
        if not self._testPresenceInChannels(irc, msg.nick):
            irc.error("In order to authenticate, you must be present in one "
                    "of the following channels: %s" % (self.registryValue('channels'),))
            return
        try:
            authrequest = self.pending_auth[msg.prefix]
        except KeyError:
            irc.error("Could not find a pending authentication request from your hostmask. "
                        "Either it expired, or you changed hostmask, or you haven't made one.")
            return
        if authrequest['type'] not in ['register','auth','changekey']:
            irc.error("No outstanding GPG signature-based request found.")
            return
        try:
            rawdata = utils.web.getUrl(url)
            m = re.search(r'-----BEGIN PGP SIGNED MESSAGE-----\r?\nHash.*?\n-----END PGP SIGNATURE-----', rawdata, re.S)
            data = m.group(0)
        except:
            irc.error("Failed to retrieve clearsigned data. Check your url.")
            return
        if authrequest['challenge'] not in data:
            irc.error("Challenge string not present in signed message.")
            return
        try:
            vo = self.gpg.verify(data)
            if not vo.valid:
                irc.error("Signature verification failed.")
                self.log.info("Signature verification from %s failed. Details: %s" % \
                        (msg.prefix, vo.stderr))
                return
            if vo.key_id != authrequest['keyid'] and vo.pubkey_fingerprint[-16:] != authrequest['keyid']:
                irc.error("Signature is not made with the key on record for this nick.")
                return
        except:
            irc.error("Authentication failed. Please try again.")
            return
        response = ""
        if authrequest['type'] == 'register':
            if self.db.getByNick(authrequest['nick']) or self.db.getByKey(authrequest['keyid']):
                irc.error("Username or key already in the database.")
                return
            self.db.register(authrequest['keyid'], authrequest['fingerprint'], None,
                        time.time(), authrequest['nick'])
            response = "Registration successful. "
        elif authrequest['type'] == 'changekey':
            gpgauth = self._ident(msg.prefix)
            if gpgauth is None:
                irc.error("You must be authenticated in order to change your registered key.")
                return
            if self.db.getByKey(authrequest['keyid']):
                irc.error("This key id already registered. Try a different key.")
                return
            self.db.changekey(gpgauth['nick'], gpgauth['keyid'], authrequest['keyid'], authrequest['fingerprint'])
            response = "Successfully changed key for user %s from %s to %s. " %\
                (gpgauth['nick'], gpgauth['keyid'], authrequest['keyid'],)
        userdata = self.db.getByNick(authrequest['nick'])
        self.authed_users[msg.prefix] = {'timestamp':time.time(),
                    'keyid': authrequest['keyid'], 'nick':authrequest['nick'],
                    'bitcoinaddress':userdata[0][3],
                    'fingerprint':authrequest['fingerprint']}
        del self.pending_auth[msg.prefix]
        logmsg = "verify success from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, authrequest['nick'], authrequest['keyid'],) + response
        self.authlog.info(logmsg)
        if not world.testing:
            irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-auth", logmsg))
        irc.reply(response + "You are now authenticated for user '%s' with key %s" %\
                        (authrequest['nick'], authrequest['keyid']))
    verify = wrap(verify, ['httpUrl'])

    def everify(self, irc, msg, args, otp):
        """<otp>

        Verify the latest encrypt-authentication request by providing your decrypted
        one-time password.
        If verified, you'll be authenticated for the duration of the bot's
        or your IRC session on channel (whichever is shorter).
        """
        self._removeExpiredRequests()
        if not self._testPresenceInChannels(irc, msg.nick):
            irc.error("In order to authenticate, you must be present in one "
                    "of the following channels: %s" % (self.registryValue('channels'),))
            return
        try:
            authrequest = self.pending_auth[msg.prefix]
        except KeyError:
            irc.error("Could not find a pending authentication request from your hostmask. "
                        "Either it expired, or you changed hostmask, or you haven't made one.")
            return
        if authrequest['type'] not in ['eregister','eauth','echangekey']:
            irc.error("No outstanding encryption-based request found.")
            return
        if authrequest['challenge'] != otp:
            irc.error("Incorrect one-time password. Try again.")
            return

        response = ""
        if authrequest['type'] == 'eregister':
            if self.db.getByNick(authrequest['nick']) or self.db.getByKey(authrequest['keyid']):
                irc.error("Username or key already in the database.")
                return
            self.db.register(authrequest['keyid'], authrequest['fingerprint'], None,
                        time.time(), authrequest['nick'])
            response = "Registration successful. "
        elif authrequest['type'] == 'echangekey':
            gpgauth = self._ident(msg.prefix)
            if gpgauth is None:
                irc.error("You must be authenticated in order to change your registered key.")
                return
            if self.db.getByKey(authrequest['keyid']):
                irc.error("This key id already registered. Try a different key.")
                return
            self.db.changekey(gpgauth['nick'], gpgauth['keyid'], authrequest['keyid'], authrequest['fingerprint'])
            response = "Successfully changed key for user %s from %s to %s. " %\
                (gpgauth['nick'], gpgauth['keyid'], authrequest['keyid'],)
        userdata = self.db.getByNick(authrequest['nick'])
        self.authed_users[msg.prefix] = {'timestamp':time.time(),
                    'keyid': authrequest['keyid'], 'nick':authrequest['nick'],
                    'bitcoinaddress':userdata[0][3],
                    'fingerprint':authrequest['fingerprint']}
        del self.pending_auth[msg.prefix]
        logmsg = "everify success from hostmask %s for user %s, keyid %s." %\
                (msg.prefix, authrequest['nick'], authrequest['keyid'],) + response
        self.authlog.info(logmsg)
        if not world.testing:
            irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-auth", logmsg))
        irc.reply(response + "You are now authenticated for user %s with key %s" %\
                        (authrequest['nick'], authrequest['keyid']))
    everify = wrap(everify, ['something'])

    def bcverify(self, irc, msg, args, data):
        """<signedmessage>

        Verify the latest authentication request by providing the <signedmessage>
        which contains the challenge string signed with your bitcoin address
        of record. If verified, you'll be authenticated for the duration of the bot's
        or your IRC session on channel (whichever is shorter).
        """
        self._removeExpiredRequests()
        if not self._testPresenceInChannels(irc, msg.nick):
            irc.error("In order to authenticate, you must be present in one "
                    "of the following channels: %s" % (self.registryValue('channels'),))
            return
        try:
            authrequest = self.pending_auth[msg.prefix]
        except KeyError:
            irc.error("Could not find a pending authentication request from your hostmask. "
                        "Either it expired, or you changed hostmask, or you haven't made one.")
            return
        if authrequest['type'] not in ['bcregister','bcauth','bcchangekey']:
            irc.error("No outstanding bitcoin-signature-based request found.")
            return
        try:
            result = bitcoinsig.verify_message(authrequest['bitcoinaddress'], data, authrequest['challenge'])
            if not result:
                irc.error("Signature verification failed.")
                return
        except:
            irc.error("Authentication failed. Please try again.")
            self.log.info("bcverify traceback: \n%s" % (traceback.format_exc()))
            return
        response = ""
        if authrequest['type'] == 'bcregister':
            if self.db.getByNick(authrequest['nick']) or self.db.getByAddr(authrequest['bitcoinaddress']):
                irc.error("Username or key already in the database.")
                return
            self.db.register(None, None, authrequest['bitcoinaddress'],
                        time.time(), authrequest['nick'])
            response = "Registration successful. "
        elif authrequest['type'] == 'bcchangekey':
            gpgauth = self._ident(msg.prefix)
            if gpgauth is None:
                irc.error("You must be authenticated in order to change your registered address.")
                return
            if self.db.getByAddr(authrequest['bitcoinaddress']):
                irc.error("This address is already registered. Try a different one.")
                return
            self.db.changeaddress(gpgauth['nick'], gpgauth['bitcoinaddress'], authrequest['bitcoinaddress'])
            response = "Successfully changed address for user %s from %s to %s. " %\
                (gpgauth['nick'], gpgauth['bitcoinaddress'], authrequest['bitcoinaddress'],)
        userdata = self.db.getByNick(authrequest['nick'])
        self.authed_users[msg.prefix] = {'timestamp':time.time(),
                    'keyid': userdata[0][1], 'nick':authrequest['nick'],
                    'bitcoinaddress':authrequest['bitcoinaddress'],
                    'fingerprint':userdata[0][2]}
        del self.pending_auth[msg.prefix]
        logmsg = "bcverify success from hostmask %s for user %s, address %s." %\
                (msg.prefix, authrequest['nick'], authrequest['bitcoinaddress'],) + response
        self.authlog.info(logmsg)
        if not world.testing:
            irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-auth", logmsg))
        irc.reply(response + "You are now authenticated for user '%s' with address %s" %\
                        (authrequest['nick'], authrequest['bitcoinaddress']))
    bcverify = wrap(bcverify, ['something'])


    #~ def changenick(self, irc, msg, args, newnick):
        #~ """<newnick>
        
        #~ Changes your GPG registered username to <newnick>.
        #~ You must be authenticated in order to use this command.
        #~ """
        #~ self._removeExpiredRequests()
        #~ gpgauth = self._ident(msg.prefix)
        #~ if gpgauth is None:
            #~ irc.error("You must be authenticated in order to change your registered username.")
            #~ return
        #~ if self.db.getByNick(newnick):
            #~ irc.error("Username already registered. Try a different username.")
            #~ return
        #~ oldnick = gpgauth['nick']
        #~ self.db.changenick(oldnick, newnick)
        #~ gpgauth['nick'] = newnick
        #~ irc.reply("Successfully changed your nick from %s to %s." % (oldnick, newnick,))
    #~ changenick = wrap(changenick, ['something'])

    def changekey(self, irc, msg, args, keyid):
        """<keyid>
        
        Changes your GPG registered key to <keyid>.
        <keyid> is a 16 digit key id, with or without the '0x' prefix.
        We look on servers listed in 'plugins.GPG.keyservers' config.
        You will be given a random passphrase to clearsign with your key, and
        submit to the bot with the 'verify' command.
        You must be authenticated in order to use this command.
        """
        self._removeExpiredRequests()
        gpgauth = self._ident(msg.prefix)
        if gpgauth is None:
            irc.error("You must be authenticated in order to change your registered key.")
            return
        if self.db.getByKey(keyid):
            irc.error("This key id already registered. Try a different key.")
            return

        keyservers = self.registryValue('keyservers').split(',')
        try:
            fingerprint = self._recv_key(keyservers, keyid)
        except Exception as e:
            irc.error("Could not retrieve your key from keyserver. "
                    "Either it isn't there, or it is invalid.")
            self.log.info("GPG changekey: failed to retrieve key %s from keyservers %s. Details: %s" % \
                    (keyid, keyservers, e,))
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'keyid':keyid,
                            'nick':gpgauth['nick'], 'expiry':time.time(),
                            'type':'changekey', 'fingerprint':fingerprint,
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("changekey request from hostmask %s for user %s, oldkeyid %s, newkeyid %s." %\
                (msg.prefix, gpgauth['nick'], gpgauth['keyid'], keyid, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (gpgauth['nick'], msg.prefix, challenge,))
    changekey = wrap(changekey, ['keyid',])

    def echangekey(self, irc, msg, args, keyid):
        """<keyid>
        
        Changes your GPG registered key to <keyid>.
        <keyid> is a 16 digit key id, with or without the '0x' prefix.
        We look on servers listed in 'plugins.GPG.keyservers' config.
        You will be given a link to a page which contains a one time password
        encrypted with your key. Decrypt, and use the 'everify' command with it.
        You must be authenticated in order to use this command.
        """
        self._removeExpiredRequests()
        gpgauth = self._ident(msg.prefix)
        if gpgauth is None:
            irc.error("You must be authenticated in order to change your registered key.")
            return
        if self.db.getByKey(keyid):
            irc.error("This key id already registered. Try a different key.")
            return

        keyservers = self.registryValue('keyservers').split(',')
        try:
            fingerprint = self._recv_key(keyservers, keyid)
        except Exception as e:
            irc.error("Could not retrieve your key from keyserver. "
                    "Either it isn't there, or it is invalid.")
            self.log.info("GPG echangekey: failed to retrieve key %s from keyservers %s. Details: %s" % \
                    (keyid, keyservers, e,))
            return
        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        try:
            data = self.gpg.encrypt(challenge + '\n', keyid, always_trust=True)
            if data.status != "encryption ok":
                raise ValueError, "problem encrypting otp"
            otpfn = conf.supybot.directories.data.dirize('otps/%s' % (keyid,))
            f = open(otpfn, 'w')
            f.write(data.data)
            f.close()
        except Exception, e:
            irc.error("Problem creating encrypted OTP file.")
            self.log.info("GPG echangekey: key %s, otp creation %s, exception %s" % \
                    (keyid, data.stderr, e,))
            return
        request = {msg.prefix: {'keyid':keyid,
                            'nick':gpgauth['nick'], 'expiry':time.time(),
                            'type':'echangekey', 'fingerprint':fingerprint,
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("echangekey request from hostmask %s for user %s, oldkeyid %s, newkeyid %s." %\
                (msg.prefix, gpgauth['nick'], gpgauth['keyid'], keyid, ))
        irc.reply("Request successful for user %s, hostmask %s. Get your encrypted OTP from %s" %\
                (gpgauth['nick'], msg.prefix, 'http://bitcoin-otc.com/otps/%s' % (keyid,),))
    echangekey = wrap(echangekey, ['keyid',])

    def changeaddress(self, irc, msg, args, bitcoinaddress):
        """<bitcoinaddress>
        
        Changes your registered address to <bitcoinaddress>.
        You will be given a random passphrase to sign with your new address, and
        submit to the bot with the 'bcverify' command.
        You must be authenticated in order to use this command.
        """
        self._removeExpiredRequests()
        gpgauth = self._ident(msg.prefix)
        if gpgauth is None:
            irc.error("You must be authenticated in order to change your registered key.")
            return
        if self.db.getByAddr(bitcoinaddress):
            irc.error("This address is already registered. Try a different one.")
            return

        challenge = "freenode:#bitcoin-otc:" + hashlib.sha256(os.urandom(128)).hexdigest()[:-8]
        request = {msg.prefix: {'bitcoinaddress':bitcoinaddress,
                            'nick':gpgauth['nick'], 'expiry':time.time(),
                            'type':'bcchangekey',
                            'challenge':challenge}}
        self.pending_auth.update(request)
        self.authlog.info("changeaddress request from hostmask %s for user %s, oldaddress %s, newaddress %s." %\
                (msg.prefix, gpgauth['nick'], gpgauth['bitcoinaddress'], bitcoinaddress, ))
        irc.reply("Request successful for user %s, hostmask %s. Your challenge string is: %s" %\
                (gpgauth['nick'], msg.prefix, challenge,))
    changeaddress = wrap(changeaddress, ['something'])


    def ident(self, irc, msg, args, nick):
        """[<nick>]
        
        Returns details about your GPG identity with the bot, or notes the
        absence thereof.
        If optional <nick> is given, tells you about <nick> instead.
        """        
        if nick is not None:
            try:
                hostmask = irc.state.nickToHostmask(nick)
            except KeyError:
                irc.error("I am not seeing this user on IRC. "
                        "If you want information about a registered gpg user, "
                        "try the 'gpg info' command instead.")
                return
        else:
            hostmask = msg.prefix
            nick = msg.nick
        response = "Nick '%s', with hostmask '%s', is " % (nick, hostmask,)
        try:
            authinfo = self.authed_users[hostmask]
            if irc.nested:
                response = authinfo['nick']
            else:
                if authinfo['nick'].upper() != nick.upper():
                    response = "\x02CAUTION: irc nick differs from otc registered nick.\x02 " + response
                response += ("identified as user '%s', with GPG key id %s, " + \
                        "key fingerprint %s, and bitcoin address %s") % (authinfo['nick'],
                                authinfo['keyid'],
                                authinfo['fingerprint'],
                                authinfo['bitcoinaddress'])
        except KeyError:
            if irc.nested:
                response = ""
            else:
                response += "not identified."
        irc.reply(response)
    ident = wrap(ident, [optional('something')])

    def _info(self, nick):
        """Return info on registered user. For use from other plugins."""
        result = self.db.getByNick(nick)
        if len(result) == 0:
            return None
        else:
            return result[0]

    def info(self, irc, msg, args, optlist, nick):
        """[--key|--address] <nick>

        Returns the registration details of registered user <nick>.
        If '--key' option is given, interpret <nick> as a GPG key ID.
        """
        if 'key' in dict(optlist).keys():
            result = self.db.getByKey(nick)
        elif 'address' in dict(optlist).keys():
            result = self.db.getByAddr(nick)
        else:
            result = self.db.getByNick(nick)
        if len(result) == 0:
            irc.reply("No such user registered.")
            return
        result = result[0]
        authhost = self._identByNick(result[5])
        if authhost is not None:
            authstatus = " Currently authenticated from hostmask %s ." % (authhost,)
            if authhost.split('!')[0].upper() != result[5].upper():
                authstatus += " CAUTION: irc nick differs from otc registered nick."
        else:
            authstatus = " Currently not authenticated."
        irc.reply("User '%s', with keyid %s, fingerprint %s, and bitcoin address %s, registered on %s. http://b-otc.com/vg?nick=%s .%s" %\
                (result[5], result[1], result[2], result[3], time.ctime(result[4]), utils.web.urlquote(result[5]), authstatus))
    info = wrap(info, [getopts({'key': '','address':'',}),'something'])

    def stats(self, irc, msg, args):
        """takes no arguments
        
        Gives the statistics on number of registered users,
        number of authenticated users, number of pending authentications.
        """
        self._removeExpiredRequests()
        try:
            regusers = self.db.getCount()[0][0]
            authedusers = len(self.authed_users)
            pendingauths = len(self.pending_auth)
        except:
            irc.error("Problem retrieving statistics. Try again later.")
            return
        irc.reply("There are %s registered users, %s currently authenticated. "
                "There are also %s pending authentication requests." % \
                (regusers, authedusers, pendingauths,))
    stats = wrap(stats)

    def _ident(self, hostmask):
        """Use to check identity status from other plugins."""
        return self.authed_users.get(hostmask, None)

    def _identByNick(self, nick):
        for k,v in self.authed_users.iteritems():
            if v['nick'].lower() == nick.lower():
                return k
        return None

    def doQuit(self, irc, msg):
        """Kill the authentication when user quits."""
        if irc.network == self.registryValue('network'):
            self._unauth(irc, msg.prefix)

    def doPart(self, irc, msg):
        """Kill the authentication when user parts all channels."""
        channels = self.registryValue('channels').split(';')
        if msg.args[0] in channels and irc.network == self.registryValue('network'):
            for channel in channels:
                try:
                    if msg.nick in irc.state.channels[channel].users:
                        break
                except KeyError:
                    pass #oh well, we're not in one of our monitored channels
            else:
                if ircutils.strEqual(msg.nick, irc.nick): #we're parting
                    self.authlog.info("***** clearing authed_users due to self-part. *****")
                    self.authed_users.clear()
                else:
                    self._unauth(irc, msg.prefix)

    def doError(self, irc, msg):
        """Reset the auth dict when bot gets disconnected."""
        if irc.network == self.registryValue('network'):
            self.authlog.info("***** clearing authed_users due to network error. *****")
            self.authed_users.clear()

    def doKick(self, irc, msg):
        """Kill the authentication when user gets kicked."""
        channels = self.registryValue('channels').split(';')
        if msg.args[0] in channels and irc.network == self.registryValue('network'):
            (channel, nick) = msg.args[:2]
            if ircutils.toLower(irc.nick) in ircutils.toLower(nick):
                self.authlog.info("***** clearing authed_users due to self-kick. *****")
                self.authed_users.clear()
            else:
                try:
                    hostmask = irc.state.nickToHostmask(nick)
                    self._unauth(irc, hostmask)
                except KeyError:
                    pass

    def doNick(self, irc, msg):
        if msg.prefix in self.authed_users.keys():
            newprefix = msg.args[0] + '!' + msg.prefix.split('!',1)[1]
            logmsg = "Attaching authentication for hostmask %s to new hostmask %s due to nick change." %\
                    (msg.prefix, newprefix,)
            self.authlog.info(logmsg)
            if not world.testing:
                irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-auth", logmsg))
            self.authed_users[newprefix] = self.authed_users[msg.prefix]
            self._unauth(irc, msg.prefix)

Class = GPG

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
