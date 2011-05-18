###
# Copyright (c) 2011, remote
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

import sys
import json

from time import sleep
from urllib2 import urlopen

def getMarketDepth():
    json_data = urlopen("http://mtgox.com/code/data/getDepth.php").read()
    mdepth = json.loads(json_data)

    return mdepth

class Market(callbacks.Plugin):
    """Add the help for "@plugin help Market" here
    This should describe *how* to use this plugin."""
    threaded = True

    def calcBitcoinAsksUnder(self, irc, msg, args, value):
        """
        Calculate the amount of bitcoins for sale under PRICE VALUE along with their total value.
        """
        mdepth = getMarketDepth()
        
        n_coins = 0.0
        total = 0.0
        asks = mdepth['asks']
        for ask in asks:
            (price, amount) = ask
            if price < value:
                n_coins += amount
                total += (amount * price)

        irc.reply("There are currently %s bitcoins for trade under $%s USD worth $%s in total." % (n_coins, 
                                                                                                   value,
                                                                                                   int(total)))
    askunder = wrap(calcBitcoinAsksUnder, ['float'])

    def calcBitcoinAsksOver(self, irc, msg, args, value):
        """
        Calculate the amount of bitcoins for sale over PRICE VALUE along with their total value.
        """
        mdepth = getMarketDepth()
        
        n_coins = 0.0
        total = 0.0
        asks = mdepth['asks']
        for ask in asks:
            (price, amount) = ask
            if price > value:
                n_coins += amount
                total += (amount * price)

        irc.reply("There are currently %s bitcoins for trade over $%s USD worth $%s in total." % (n_coins, 
                                                                                                   value,
                                                                                                   int(total)))
    askover = wrap(calcBitcoinAsksOver, ['float'])

    def calcBitcoinBidsOver(self, irc, msg, args, value):
        """
        Calculate the amount of bitcoins that will be sold before bid price reaches `value' and their total value.
        
        returns a tuple in format: (amount, value)
        """
        mdepth = getMarketDepth()
        
        n_coins = 0
        total = 0
        bids = mdepth['bids']
        for bid in bids:
            (price, amount) = bid
            if price > value:
                n_coins += amount
                total += (amount * price)
        
        irc.reply("There are currently %s bitcoins bids offered over $%s USD worth $%s in total." % (n_coins, 
                                                                                                     value,
                                                                                                     int(total)))
    bidover = wrap(calcBitcoinBidsOver, ['float'])

Class = Market


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
