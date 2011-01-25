###
# Copyright (c) 2010, Daniel Folkinshteyn
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

import sqlite3

class OTCOrderBookTestCase(PluginTestCase):
    plugins = ('OTCOrderBook','User')

    def testBuy(self):
        # no cloak
        self.assertError('buy 1000 btc at 0.06 LRUSD really nice offer!')
        try:
            world.testing = False
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertRegexp('buy 1000 btc at 0.06 LRUSD really nice offer!', 'Order id \d+ created')
            self.assertNotError('buy 2000 bitcoins @ 0.06 LRUSD')
            self.assertNotError('buy 3000 bitcoin at 0.07 PPUSD really nice offer!')
            self.assertNotError('buy 4000 btc at 10 LRUSD some text')
            self.assertNotError('view')
            self.assertError('buy 5000 btc at 0.06 LRUSD mooo') # max orders
            self.assertRegexp('view', '1000.*2000')
            self.prefix = 'stuff!stuff@gateway/web/freenode/moo'
            self.assertError('buy 1000 btc at 0.06 lrusd bla') # no cloak
            self.assertNotError('register nottester stuff')
            self.assertNotError('buy 1000 btc at 0.06 lrusd bla') # registered user
        finally:
            world.testing = True
            self.prefix = origuser

    def testSell(self):
        # no cloak
        self.assertError('buy 1000 btc at 0.06 LRUSD really nice offer!')
        try:
            world.testing = False
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertRegexp('sell 1000 btc at 0.06 LRUSD really nice offer!', 'Order id \d+ created')
            self.assertNotError('sell 2000 bitcoins @ 0.06 LRUSD')
            self.assertNotError('sell 3000 bitcoin at 0.07 PPUSD really nice offer!')
            self.assertNotError('sell 4000 btc at 10 LRUSD some text')
            self.assertNotError('view')
            self.assertError('sell 5000 btc at 0.06 LRUSD mooo') # max orders
            self.assertRegexp('view', '1000.*2000')
            self.prefix = 'stuff!stuff@stuff'
            self.assertError('sell 1000 btc at 0.06 lrusd bla') # no cloak
            self.assertNotError('register nottester stuff')
            self.assertNotError('sell 1000 btc at 0.06 lrusd bla') # registered user
            self.assertNotError('sell 1000 btc at 0 usd loan for 1 month at 1% monthly interest')
        finally:
            world.testing = True
            self.prefix = origuser

    def testRefresh(self):
        try:
            world.testing = False
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertNotError('buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('refresh')
            self.assertNotError('refresh 1')
            self.assertRegexp('view', '1000')
        finally:
            world.testing = True
            self.prefix = origuser

    def testRemove(self):
        try:
            world.testing = False
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertNotError('buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('sell 2000 btc at 0.06 LRUSD really nice offer!')
            self.assertRegexp('view', '1000.*2000')
            self.assertNotError('remove 1')
            self.assertNotRegexp('view', '1000.*2000')
            self.assertRegexp('view', '2000')
            self.assertNotError('buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('remove')
            self.assertError('view')
        finally:
            world.testing = True
            self.prefix = origuser

    def testBook(self):
        try:
            world.testing = False
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertNotError('buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('sell 2000 btc at 0.07 LRUSD really nice offer!')
            self.assertNotError('buy 3000 btc at 0.06 PPUSD really nice offer!')
            self.assertNotError('sell 4000 btc at 0.06 PPUSD really nice offer!')
            self.assertRegexp('view', '1000.*2000.*3000.*4000')
            self.assertNotRegexp('book LRUSD', '1000.*2000.*3000.*4000')
            self.assertRegexp('book LRUSD', '1000.*2000')
            self.assertNotError('remove 4')
            self.assertNotError('buy 5000 btc at 0.05 LRUSD')
            self.assertRegexp('book LRUSD', '5000.*1000.*2000')
#            self.assertRegexp('book lrusd', '5000.*1000.*2000')
        finally:
            world.testing = True
            self.prefix = origuser

    def testIndexing(self):
        try:
            origuser = self.prefix
            self.prefix = 'stuff!stuff@stuff/somecloak'
            self.assertNotError('buy 1000 btc at "{mtgoxbid} - 0.03" ppusd')
            self.assertRegexp('view', 'BUY 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'BUY 1000.0 btc @ {mtgoxbid}')
            self.assertNotError('remove')
            self.assertNotError('sell 1000 btc at "{mtgoxask} + 0.03" ppusd')
            self.assertRegexp('view', 'SELL 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'SELL 1000.0 btc @ {mtgoxask}')
            self.assertNotError('remove')
            self.assertNotError('buy 1000 btc at "0.5*({mtgoxlast} + {mtgoxbid})" ppusd split the spread')
            self.assertRegexp('view', 'BUY 1000.0 btc @ \d')
            self.assertNotError('remove')
            self.assertNotError('buy 1000 btc at "{mtgoxlast} - 0.03" ppusd')
            self.assertRegexp('view', 'BUY 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'BUY 1000.0 btc @ {mtgoxlast}')
            self.assertRegexp('book ppusd', 'BUY 1000.0 btc @ \d')
            self.assertError('buy 1000 btc at "{zomg} + 1" ppusd');
        finally:
            self.prefix = origuser

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
