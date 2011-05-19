###
# Copyright (c) 2011, remote
# Copyright (c) 2011, nanotube
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

import json
from urllib2 import urlopen

def getNonNegativeFloat(irc, msg, args, state, type=' floating point number'):
    try:
        v = float(args[0])
        if v < 0:
            raise ValueError, "only non-negative numbers allowed."
        state.args.append(v)
        del args[0]
    except ValueError:
        state.errorInvalid(type, args[0])

addConverter('nonNegativeFloat', getNonNegativeFloat)

class Market(callbacks.Plugin):
    """Add the help for "@plugin help Market" here
    This should describe *how* to use this plugin."""
    threaded = True

    def _getMarketDepth(self):
        json_data = urlopen("http://mtgox.com/code/data/getDepth.php").read()
        mdepth = json.loads(json_data)
        return mdepth

    def _getTicker(self):
        json_data = urlopen("http://mtgox.com/code/data/ticker.php").read()
        ticker = json.loads(json_data)
        return ticker['ticker']

    def asks(self, irc, msg, args, optlist, pricetarget):
        """[--over] <pricetarget>
        
        Calculate the amount of bitcoins for sale at or under <pricetarget>.
        If '--over' option is given, find coins or at or over <pricetarget>.
        """
        try:
            mdepth = self._getMarketDepth()
        except:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        response = "under"
        if dict(optlist).has_key('over'):
            f = lambda price,pricetarget: price >= pricetarget
            response = "over"
        else:
            f = lambda price,pricetarget: price <= pricetarget
        n_coins = 0.0
        total = 0.0
        asks = mdepth['asks']
        for ask in asks:
            (price, amount) = ask
            if f(price, pricetarget):
                n_coins += amount
                total += (amount * price)

        irc.reply("There are currently %.8g bitcoins offered at "
                "or %s %s USD, worth %s USD in total." % (n_coins, 
                        response, pricetarget, total))
    asks = wrap(asks, [getopts({'over': '',}), 'nonNegativeFloat'])

    def bids(self, irc, msg, args, optlist, pricetarget):
        """[--under] <pricetarget>
        
        Calculate the amount of bitcoin demanded at or over <pricetarget>.
        If '--under' option is given, find coins or at or under <pricetarget>.
        """
        try:
            mdepth = self._getMarketDepth()
        except:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        response = "over"
        if dict(optlist).has_key('under'):
            f = lambda price,pricetarget: price <= pricetarget
            response = "under"
        else:
            f = lambda price,pricetarget: price >= pricetarget
        n_coins = 0.0
        total = 0.0
        bids = mdepth['bids']
        for bid in bids:
            (price, amount) = bid
            if f(price, pricetarget):
                n_coins += amount
                total += (amount * price)

        irc.reply("There are currently %.8g bitcoins demanded at "
                "or %s %s USD, worth %s USD in total." % (n_coins, 
                        response, pricetarget, total))
    bids = wrap(bids, [getopts({'under': '',}), 'nonNegativeFloat'])

    def ticker(self, irc, msg, args):
        """takes no arguments
        
        Return pretty-printed mtgox ticker.
        """
        try:
            ticker = self._getTicker()
        except:
            irc.error("Failure to retrieve ticker. Try again later.")
            return
        irc.reply("Best bid: %s, Best ask: %s, Bid-ask spread: %s, Last trade: %s, "
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s" % \
                (ticker['buy'], ticker['sell'], ticker['sell'] - ticker['buy'], ticker['last'], 
                ticker['vol'], ticker['low'], ticker['high']))
    ticker = wrap(ticker)

Class = Market


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
