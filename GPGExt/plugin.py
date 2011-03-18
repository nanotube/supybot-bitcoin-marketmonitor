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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re
import base64

# regexp to match the gpg_identity tag
# make sure to drop any html tags a site may add after.
gpgtagre = re.compile(r'gpg_identity=([^\s<]+)')

class GPGExt(callbacks.Plugin):
    """This plugin uses the external gpg identity protocol to verify
    a user's identity on external site using his registered GPG key.
    http://wiki.bitcoin-otc.com/wiki/GPG_Identity_Protocol
    Depends on the GPG plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(GPGExt, self)
        self.__parent.__init__(irc)

    def _checkGPGAuth(self, irc, prefix):
        return irc.getCallback('GPG')._ident(prefix)

    def _checkGPGReg(self, irc, nick):
        return irc.getCallback('GPG').db.getByNick(nick)

    def _verifyGPGSigData(self, irc, data, keyid):
        """verify data, return site and nick dict if all good, return dict with 'error' otherwise."""
        site = re.search(r'^site: (.*)$', data, re.M)
        user = re.search(r'^user: (.*)$', data, re.M)
        if site is None or user is None:
            return {'error':'Site or user data not found in signed message'}
        try:
            vo = irc.getCallback('GPG').gpg.verify(data)
            if not vo.valid:
                return {'error': 'Signature verification failed.'}
            if vo.key_id != keyid:
                return {'error': 'Signature is not made with the key on record for this nick.'}
        except:
            return {'error':'Signature verification failed.'}
        return {'site':site.group(1), 'user':user.group(1)}

    def verify(self, irc, msg, args, url, nick):
        """<url> [<nick>]
        
        Pulls the gpg signature data from <url>, and verifies it against <nick>'s
        registered gpg key. If <nick> is omitted, uses the requestor's registered nick.
        """
        if nick is None:
            gpgauth = self._checkGPGAuth(irc, msg.prefix)
            if gpgauth is not None:
                nick = gpgauth['nick']
            else:
                nick = msg.nick
        gpgreg = self._checkGPGReg(irc, nick)
        if len(gpgreg) == 0:
            irc.error("Nick %s not registered in GPG database." % (nick,))
            return
        keyid = gpgreg[0][1]
        try:
            pagedata = utils.web.getUrl(url)
        except:
            irc.error("Problem retrieving target url.")
            return
        m = gpgtagre.search(pagedata)
        if m is None:
            irc.error("GPG identity tag not found on target page.")
            return
        data = m.group(1)
        if '.' in data: # this is a url
            try:
                signedmsg = utils.web.getUrl(data)
            except:
                irc.error("Can't retrieve signature from link '%s' in GPG identity tag." % (data,))
                return
        else:
            try:
                signedmsg = base64.b64decode(data)
            except:
                irc.error("Problems base64 decoding key data.")
                return
        try:
            m = re.search(r'-----BEGIN PGP SIGNED MESSAGE-----.*?\n-----END PGP SIGNATURE-----', signedmsg, re.S)
            signedmsg = m.group(0)
        except:
            irc.error("Malformed signed message.")
            return
        result = self._verifyGPGSigData(irc, signedmsg, keyid)
        if result.has_key('error'):
            irc.error("GPG identity tag failed to verify with key id %s. Reason: %s" % \
                    (keyid, result['error']))
            return
        irc.reply("Verified signature made with keyid %s, belonging to OTC user %s, "
                "for site %s and user %s. "
                "Note that you must still verify manually that (1) the site and username "
                "match the content of signed message, and (2) that the GPG identity tag "
                "was posted in user-only accessible area of the site." % \
                (keyid, nick, result['site'], result['user'],))
    verify = wrap(verify, ['httpUrl',optional('something')])

Class = GPGExt


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
