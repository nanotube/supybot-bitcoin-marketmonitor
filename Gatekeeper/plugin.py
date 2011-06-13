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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import ircmsgs
import time

class Gatekeeper(callbacks.Plugin):
    """Lets you into #bitcoin-otc, if you're authenticated and
    meet minimum requirements."""
    threaded = True

    def _checkGPGAuth(self, irc, prefix):
        return irc.getCallback('GPG')._ident(prefix)

    def _getGPGInfo(self, irc, nick):
        return irc.getCallback('GPG')._info(nick)

    def _getCumulativeRating(self, irc, nick):
        return irc.getCallback('RatingSystem')._getrating(nick)

    def letmein(self, irc, msg, args):
        """takes no arguments
        
        invites you to the main #bitcoin-otc channel, if you qualify.
        """
        gpgauth = self._checkGPGAuth(irc, msg.prefix)
        if gpgauth is None:
            irc.error("You must authenticate via GPG to enter.")
            return
        info = self._getGPGInfo(irc, gpgauth['nick'])
        if info is not None:
            regtimestamp = info[3]
        else:
            # this should not happen
            irc.error("No info on your user in the database.")
            return
        rating = self._getCumulativeRating(irc, gpgauth['nick'])
        if rating is None:
            rating = 0
        if rating >= self.registryValue('ratingThreshold') and \
                time.time() - regtimestamp > self.registryValue('accountAgeThreshold'):
                irc.queueMsg(ircmsgs.voice('#bitcoin-otc-foyer', msg.nick))
                irc.queueMsg(ircmsgs.invite(msg.nick, '#bitcoin-otc'))
                irc.noReply()
            #voice, and invite
        else:
            irc.error("Insufficient account age or rating. Required minimum account age is %s days, and required minimum rating is %s. Yours are %s days and %s, respectively." % (self.registryValue('accountAgeThreshold')/60/60/24, self.registryValue('ratingThreshold'),(time.time() - regtimestamp)/60/60/24, rating))
            return
    letmein = wrap(letmein)

Class = Gatekeeper


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
