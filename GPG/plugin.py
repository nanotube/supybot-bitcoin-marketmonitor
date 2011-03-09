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
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import sqlite3
import re
import os
import hashlib
import time
import copy

try:
    gnupg = utils.python.universalImport('gnupg', 'local.gnupg')
except ImportError:
    raise callbacks.Error, \
            "You need the gnupg module installed to use this plugin." 

domainRe = re.compile('^' + utils.web._domain + '$', re.I)

class GPGDB(object):
    def __init__(self, filename):
        self.filename = filename
        self.db = None

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
        cursor.execute("""CREATE TABLE users (
                          id INTEGER PRIMARY KEY,
                          keyid TEXT,
                          fingerprint TEXT,
                          registered_at INTEGER,
                          nick TEXT)
                           """)
        self.db.commit()
        return

    def close(self):
        self.db.close()

    def getByNick(self, nick):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM users WHERE nick LIKE ?""", (nick,))
        return cursor.fetchall()

    def getByKey(self, keyid):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM users WHERE keyid = ?""", (keyid,))
        return cursor.fetchall()

    def getCount(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT count(*) FROM users""")
        return cursor.fetchall()

    def register(self, keyid, fingerprint, timestamp, nick):
        cursor = self.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                        (NULL, ?, ?, ?, ?)""",
                        (keyid, fingerprint, timestamp, nick))
        self.db.commit()

def getGPGKeyID(irc, msg, args, state, type='GPG key id'):
    v = args[0]
    m = re.search(r'^(0x)?([0-9A-Fa-f]{16})$', v)
    if m is None:
        state.errorInvalid(type, args[0])
        return
    state.args.append(m.group(2).upper())
    del args[0]

def getKeyserver(irc, msg, args, state, type='keyserver'):
    v = args[0]
    if not domainRe.search(v):
        state.errorInvalid(type, args[0])
        return
    state.args.append(args[0])
    del args[0]

addConverter('keyid', getGPGKeyID)
addConverter('keyserver', getKeyserver)

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
        self.gpg = gnupg.GPG(gnupghome = conf.supybot.directories.data.dirize('GPGkeyring'))
        self.pending_auth = {}
        self.authed_users = {}

    def die(self):
        self.__parent.die()
        self.db.close()

    def _removeExpiredRequests(self):
        pending_auth_copy = copy.deepcopy(self.pending_auth)
        for hostmask,auth in pending_auth_copy.iteritems():
            try:
                if time.time() - auth['expiry'] > self.registryValue('authRequestTimeout'):
                    if auth['registration'] and not self.db.getByKey(auth['keyid']):
                        try:
                            gpg.delete_keys(auth['fingerprint'])
                        except:
                            pass
                    del self.pending_auth[hostmask]
            except:
                pass #let's keep going

    def register(self, irc, msg, args, nick, keyid, keyserver):
        """<nick> <keyid> [<keyserver>]

        Register your GPG identity, associating GPG key <keyid> with <nick>.
        <keyid> is a 16 digit key id, with or without the '0x' prefix.
        Optional <keyserver> argument tells us where to get your public key.
        By default we look on pgp.mit.edu and pgp.surfnet.nl.
        You will be given a random passphrase to clearsign with your key, and
        submit to the bot with the 'verify' command.
        Your passphrase will expire within 5 minutes.
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
        if len(rsdata) != 0 and rsdata[0][8] != msg.host:
            irc.error("This username is reserved for the existing member of the "
                    "web of trust, with host '%s'." % (rsdata[0][8],))
            return
        keyservers = []
        if keyserver:
            keyservers.extend([keyserver])
        else:
            keyservers.extend(self.registryValue('keyservers').split(','))
        try:
            for ks in keyservers:
                result = self.gpg.recv_keys(ks, keyid)
                if result.results[0].has_key('ok'):
                    fingerprint = result.results[0]['fingerprint']
                    break
            else:
                raise
        except:
            irc.error("Could not retrieve your key from keyserver.")
            return
        challenge = hashlib.sha256(os.urandom(128)).hexdigest()
        request = {msg.prefix: {'keyid':keyid,
                            'nick':nick, 'expiry':time.time(),
                            'registration':True, 'fingerprint':fingerprint,
                            'challenge':challenge}}
        self.pending_auth.update(request)
        irc.reply("Request successful for user %s. Your challenge string is: %s" %\
                (nick, challenge,))
    register = wrap(register, ['something', 'keyid', optional('keyserver')])

    def auth(self, irc, msg, args, nick):
        """<nick>

        Initiate authentication for user <nick>.
        You must have registered a GPG key with the bot for this to work.
        You will be given a random passphrase to clearsign with your key, and
        submit to the bot with the 'verify' command.
        Your passphrase will expire within 5 minutes.
        """
        self._removeExpiredRequests()
        userdata = self.db.getByNick(nick)
        if len(userdata) == 0:
            irc.error("This nick is not registered. Please register.")
            return
        keyid = userdata[0][1]
        fingerprint = userdata[0][2]
        challenge = hashlib.sha256(os.urandom(128)).hexdigest()
        request = {msg.prefix: {'nick':nick,
                                'expiry':time.time(), 'keyid':keyid,
                                'registration':False, 'challenge':challenge,
                                'fingerprint':fingerprint}}
        self.pending_auth.update(request)
        irc.reply("Request successful for user %s. Your challenge string is: %s" %\
                (nick, challenge,))
    auth = wrap(auth, ['something'])

    def _unauth(self, hostmask):
        try:
            del self.authed_users[hostmask]
            return True
        except KeyError:
            return False

    def unauth(self, irc, msg, args):
        """takes no arguments
        
        Unauthenticate, 'logout' of your GPG session.
        """
        if self._unauth(msg.prefix):
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
        try:
            data = utils.web.getUrl(url)
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
                return
            if vo.key_id != authrequest['keyid']:
                irc.error("Signature is not made with the key on record for this nick.")
                return
        except:
            irc.error("Authentication failed. Please try again.")
            return
        response = ""
        if authrequest['registration']:
            if self.db.getByNick(authrequest['nick']) or self.db.getByKey(authrequest['keyid']):
                irc.error("Username or key already in the database.")
                return
            self.db.register(authrequest['keyid'], authrequest['fingerprint'],
                        time.time(), authrequest['nick'])
            response = "Registration successful. "
        self.authed_users[msg.prefix] = {'timestamp':time.time(),
                    'keyid': authrequest['keyid'], 'nick':authrequest['nick'],
                    'fingerprint':authrequest['fingerprint']}
        del self.pending_auth[msg.prefix]
        irc.reply(response + "You are now authenticated for user '%s' with key %s" %\
                        (authrequest['nick'], authrequest['keyid']))
    verify = wrap(verify, ['httpUrl'])

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
            response = "Nick '%s', with hostmask '%s', is " % (nick, hostmask,)
        else:
            hostmask = msg.prefix
            response = "You are "
        try:
            authinfo = self.authed_users[hostmask]
            irc.reply(response + "identified as user %s, with GPG key id %s, "
                            "and key fingerprint %s." % (authinfo['nick'],
                                        authinfo['keyid'],
                                        authinfo['fingerprint']))
        except KeyError:
            irc.reply(response + "not identified.")
    ident = wrap(ident, [optional('something')])

    def info(self, irc, msg, args, nick):
        """<nick>
        
        Returns the registration details of registered user <nick>.
        """
        result = self.db.getByNick(nick)
        if len(result) == 0:
            irc.error("No such user registered.")
            return
        result = result[0]
        irc.reply("User '%s', with keyid %s and fingerprint %s, registered on %s." %\
                (result[4], result[1], result[2], time.ctime(result[3])))
    info = wrap(info, ['something'])

    def stats(self, irc, msg, args):
        """takes no arguments
        
        Gives the statistics on number of registered users,
        number of authenticated users, number of pending authentications.
        """
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
        try:
            return self.authed_users[hostmask]
        except KeyError:
            return None

    def doQuit(self, irc, msg):
        """Kill the authentication when user quits."""
        if irc.network == self.registryValue('network'):
            self._unauth(msg.prefix)

    def doPart(self, irc, msg):
        """Kill the authentication when user parts channel."""
        channels = self.registryValue('channels').split(';')
        if msg.args[0] in channels and irc.network == self.registryValue('network'):
            if ircutils.strEqual(msg.nick, irc.nick): #we're parting
                self.authed_users.clear()
            else:
                self._unauth(msg.prefix)

    def doError(self, irc, msg):
        """Reset the auth dict when bot gets disconnected."""
        if irc.network == self.registryValue('network'):
            self.authed_users.clear()

    def doKick(self, irc, msg):
        """Kill the authentication when user gets kicked."""
        channels = self.registryValue('channels').split(';')
        if msg.args[0] in channels and irc.network == self.registryValue('network'):
            (channel, nicks) = msg.args[:2]
            if ircutils.toLower(irc.nick) in ircutils.toLower(nicks).split(','):
                self.authed_users.clear()
            else:
                for nick in nicks:
                    try:
                        hostmask = irc.state.nickToHostmask(nick)
                        self._unauth(hostmask)
                    except KeyError:
                        pass

    def doNick(self, irc, msg):
        if msg.prefix in self.authed_users.keys():
            newprefix = msg.args[0] + '!' + msg.prefix.split('!',1)[1]
            self.authed_users[newprefix] = self.authed_users[msg.prefix]
            self._unauth(msg.prefix)

Class = GPG

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
