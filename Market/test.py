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

from supybot.test import *

class MarketTestCase(PluginTestCase):
    plugins = ('Market',)

    def testAsks(self):
        self.assertError('asks blabla')
        self.assertError('asks --market nosuchthing 1000')
        self.assertRegexp('asks 0', 'There are currently 0 bitcoins offered at or under 0')
        self.assertRegexp('asks --over 5.5', 'There are currently .* bitcoins offered at or over 5')
        self.assertRegexp('asks --market bitstamp 10000', 'There are currently .* bitcoins offered')
        self.assertRegexp('asks --market bitstamp --currency EUR 10000', 'There are currently .* bitcoins offered')
        self.assertRegexp('asks --market btsp --over 5.5', 'There are currently .* bitcoins offered at or over 5')

    def testBids(self):
        self.assertError('bids blabla')
        self.assertError('bids --market nosuchthing 1000')
        self.assertRegexp('bids 10000000', 'There are currently 0 bitcoins demanded at or over 1')
        self.assertRegexp('bids --under 5.5', 'There are currently .* bitcoins demanded at or under 5')
        self.assertRegexp('bids --market bitstamp 1000', 'There are currently .* bitcoins demanded')
        self.assertRegexp('bids --market bitstamp --currency EUR 1000', 'There are currently .* bitcoins demanded')
        self.assertRegexp('bids --market bitstamp --under 5.5', 'There are currently .* bitcoins demanded at or under 5')

    def testTicker(self):
        self.assertRegexp('ticker', 'Best bid')
        self.assertRegexp('ticker --bid', '[\d\.]+')
        self.assertRegexp('ticker --ask', '[\d\.]+')
        self.assertRegexp('ticker --last', '[\d\.]+')
        self.assertRegexp('ticker --high', '[\d\.]+')
        self.assertRegexp('ticker --low', '[\d\.]+')
        self.assertRegexp('ticker --avg', '[\d\.]+')
        self.assertRegexp('ticker --vol', '[\d\.]+')
        self.assertError('ticker --last --bid') # can't have multiple result options
        self.assertRegexp('ticker', 'BTCUSD')
        self.assertRegexp('ticker --currency EUR', 'BTCEUR')
        self.assertRegexp('ticker --currency EUR --currency JPY', 'BTCJPY') # should use the last supplied currency
        self.assertRegexp('ticker --currency EUR --avg', '[\d\.]+')
        self.assertError('ticker --last --bid --currency USD') # can't have multiple result options
        self.assertError('ticker --currency ZZZ') # no such currency
        self.assertError('ticker --currency blablabla') # invalid currency code
        self.assertRegexp('ticker --market bitstamp --currency USD', 'Bitstamp BTCUSD')
        
    def testBuy(self):
        self.assertError('buy blabla')
        self.assertRegexp('buy 100', 'market order to buy .* bitcoins right now would')
        self.assertRegexp('buy --fiat 100', 'market order to buy .* USD worth of bitcoins right now would buy')
        self.assertRegexp('buy --market bitstamp 100', 'market order to buy .* bitcoins right now would')
        self.assertRegexp('buy --market bitstamp --currency EUR 100', 'market order to buy .* bitcoins right now would')
        self.assertRegexp('buy --market btsp --fiat --currency eur 100', 'market order to buy .* EUR worth of bitcoins right now would buy')

    def testSell(self):
        self.assertError('sell blabla')
        self.assertRegexp('sell 100', 'market order to sell .* bitcoins right now would')
        self.assertRegexp('sell --fiat 100', 'market order to sell .* USD worth of bitcoins right now would')
        self.assertRegexp('sell --market btsp 100', 'market order to sell .* bitcoins right now would')
        self.assertRegexp('sell --market btsp --currency eur 100', 'market order to sell .* bitcoins right now would')
        self.assertRegexp('sell --market bitstamp --fiat --currency eur 100', 'market order to sell .* EUR worth of bitcoins right now would')

    def testObip(self):
        self.assertError('obip blabla')
        self.assertRegexp('obip 100', 'weighted average price of BTC, .* coins up and down')
        self.assertRegexp('obip --market btsp 100', 'weighted average price of BTC, .* coins up and down')
        self.assertRegexp('obip --market btsp --currency EUR 100', 'weighted average price of BTC, .* coins up and down')
        self.assertError('obip 0')
        self.assertError('obip -100')

    def testBaratio(self):
        self.assertError('baratio blabla')
        self.assertRegexp('baratio', 'Total bids.*Total asks')
        self.assertRegexp('baratio --market bitstamp', 'Bitstamp | Total bids.*Total asks')
        self.assertRegexp('baratio --market krk', 'Kraken | Total bids.*Total asks')
        self.assertRegexp('baratio --market bitstamp --currency eur', 'Bitstamp | Total bids.*Total asks')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
