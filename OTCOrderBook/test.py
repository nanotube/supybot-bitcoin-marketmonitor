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
import unittest

import sqlite3

class OTCOrderBookTestCase(PluginTestCase):
    plugins = ('OTCOrderBook','GPG','RatingSystem','Market')

    def setUp(self):
        PluginTestCase.setUp(self)

        #preseed the GPG db with a GPG registration and auth for nanotube
        gpg = self.irc.getCallback('GPG')
        gpg.db.register('AAAAAAAAAAAAAAA1', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA1',
                    '1somestuff', time.time(), 'nanotube')
        gpg.authed_users['nanotube!stuff@stuff/somecloak'] = {'nick':'nanotube'}
        gpg.db.register('AAAAAAAAAAAAAAA2', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA2',
                   '1somestuff',  time.time(), 'registeredguy')
        gpg.db.register('AAAAAAAAAAAAAAA3', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA3',
                    '1somestuff', time.time(), 'authedguy')
        gpg.authed_users['authedguy!stuff@123.345.234.34'] = {'nick':'authedguy'}
        gpg.db.register('AAAAAAAAAAAAAAA4', 'AAAAAAAAAAAAAAAAAAA1AAAAAAAAAAAAAAA4',
                    '1somestuff', time.time(), 'authedguy2')
        gpg.authed_users['authedguy2!stuff@123.345.234.34'] = {'nick':'authedguy2'}

        # pre-seed the rating db with some ratings, for testing long orders
        cb = self.irc.getCallback('RatingSystem')
        cursor = cb.db.db.cursor()
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'nanotube','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'authedguy','stuff/somecloak'))
        cursor.execute("""INSERT INTO users VALUES
                          (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (10, time.time(), 1, 0, 0, 0, 'authedguy2','stuff/somecloak'))
        cursor.execute("""INSERT INTO ratings VALUES
                          (NULL, ?, ?, ?, ?, ?)""",
                       (2,1, time.time(), 10, 'great guy'))
        cursor.execute("""INSERT INTO ratings VALUES
                          (NULL, ?, ?, ?, ?, ?)""",
                       (3,2, time.time(), 10, 'great guy'))
        cursor.execute("""INSERT INTO ratings VALUES
                          (NULL, ?, ?, ?, ?, ?)""",
                       (3,1, time.time(), 10, 'great guy'))
        cb.db.db.commit()
    
    def testBuy(self):
        # no gpg auth
        self.assertError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertRegexp('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!', 'Order id \d+ created')
            self.assertNotError('otcorderbook buy 2000 bitcoins @ 0.06 LRUSD')
            self.assertNotError('otcorderbook buy 3000 bitcoin at 0.07 PPUSD really nice offer!')
            self.assertNotError('otcorderbook buy 4000 btc at 10 LRUSD some text')
            self.assertNotError('view')
            self.assertRegexp('view 1', 'buy 1000')
            self.assertError('otcorderbook buy 5000 btc at 0.06 LRUSD mooo') # max orders
            self.assertRegexp('view', '1000.*2000')
            self.assertError('otcorderbook buy --long 5000 btc at 0.06 USD this is a long order') #not enough trust
            self.prefix = 'authedguy2!stuff@123.345.234.34'
            self.assertNotError('otcorderbook buy --long 5000 btc at 0.06 USD this is a long order') #now we have 20 total trust
            self.assertRegexp('view', '5000')
        finally:
            self.prefix = origuser

    def testSell(self):
        # no gpg auth
        self.assertError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertRegexp('otcorderbook sell 1000 btc at 0.06 LRUSD really nice offer!', 'Order id \d+ created')
            self.assertNotError('otcorderbook sell 2000 bitcoins @ 0.06 LRUSD')
            self.assertNotError('otcorderbook sell 3000 bitcoin at 0.07 PPUSD really nice offer!')
            self.assertNotError('otcorderbook sell 4000 btc at 10 LRUSD some text')
            self.assertNotError('view')
            self.assertError('otcorderbook sell 5000 btc at 0.06 LRUSD mooo') # max orders
            self.assertRegexp('view', '1000.*2000')
            self.assertError('otcorderbook sell --long 5000 btc at 0.06 USD this is a long order') #not enough trust
            self.prefix = 'authedguy2!stuff@123.345.234.34'
            self.assertNotError('otcorderbook sell --long 5000 btc at 0.06 USD this is a long order') #now we have 20 total trust
            self.assertRegexp('view', '5000')
        finally:
            self.prefix = origuser

    def testRefresh(self):
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('refresh')
            self.assertNotError('refresh 1')
            self.assertRegexp('view', '1000')
            self.assertError('refresh --long') #not enough trust
            self.prefix = 'authedguy2!stuff@123.345.234.34' #now we have 20 total trust
            self.assertNotError('otcorderbook buy 5000 btc at 0.06 USD this is a long order') 
            self.assertNotError('refresh --long')
        finally:
            self.prefix = origuser

    def testRemove(self):
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('otcorderbook sell 2000 btc at 0.06 LRUSD really nice offer!')
            self.assertRegexp('view', '1000.*2000')
            self.assertNotError('remove 1')
            self.assertNotRegexp('view', '1000.*2000')
            self.assertRegexp('view', '2000')
            self.assertNotError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('remove 2')
            self.assertNotError('remove 3')
            self.assertError('view')
        finally:
            self.prefix = origuser

    def testBook(self):
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('otcorderbook buy 1000 btc at 0.06 LRUSD really nice offer!')
            self.assertNotError('otcorderbook sell 2000 btc at 0.07 LRUSD really nice offer!')
            self.assertNotError('otcorderbook buy 3000 btc at 0.06 PPUSD really nice offer!')
            self.assertNotError('otcorderbook sell 4000 btc at 0.06 PPUSD really nice offer!')
            self.assertRegexp('view', '1000.*2000.*3000.*4000')
            self.assertNotRegexp('book LRUSD', '1000.*2000.*3000.*4000')
            self.assertRegexp('book LRUSD', '1000.*2000')
            self.assertNotError('remove 4')
            self.assertNotError('otcorderbook buy 5000 btc at 0.05 LRUSD')
            self.assertRegexp('book LRUSD', '5000.*1000.*2000')
        finally:
            self.prefix = origuser

    def testIndexing(self):
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('otcorderbook buy 1000 btc at "{mtgoxbid} - 0.03" ppusd')
            self.assertRegexp('view', 'buy 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'buy 1000.0 btc @ "{mtgoxbid}')
            self.assertNotError('remove 1')
            self.assertNotError('otcorderbook sell 1000 btc at "{mtgoxask} + 0.03" ppusd')
            self.assertRegexp('view', 'sell 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'sell 1000.0 btc @ "{mtgoxask}')
            self.assertNotError('remove 2')
            self.assertNotError('otcorderbook buy 1000 btc at "0.5*({mtgoxask} + {mtgoxbid})" ppusd split the spread')
            self.assertRegexp('view', 'buy 1000.0 btc @ \d')
            self.assertNotError('remove 3')
            self.assertNotError('otcorderbook buy 1000 btc at "{mtgoxlast} - 0.03" ppusd')
            self.assertRegexp('view', 'buy 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'buy 1000.0 btc @ "{mtgoxlast}')
            self.assertRegexp('book ppusd', 'buy 1000.0 btc @ \d')
            self.assertNotError('remove 4')
            self.assertNotError('otcorderbook buy 1000 btc at "({mtgoxlast} - 0.03) * {usd in eur}" ppeur')
            self.assertRegexp('view', 'buy 1000.0 btc @ \d')
            self.assertRegexp('view --raw', 'buy 1000.0 btc @ "\({mtgoxlast}')
            self.assertNotError('remove 5')
            self.assertNotError('otcorderbook buy 1000 btc at "0.5*({mtgoxlast} + {bitstamplast})" ppusd average the markets')
            self.assertRegexp('view', 'buy 1000.0 btc @ \d')
            self.assertError('otcorderbook buy 1000 btc at "{zomg} + 1" ppusd');
        finally:
            self.prefix = origuser

    def testView(self):
        try:
            origuser = self.prefix
            self.prefix = 'nanotube!stuff@stuff/somecloak'
            self.assertNotError('otcorderbook buy 1000 btc at .8 usd')
            self.assertNotError('otcorderbook sell 2000 btc at .9 usd')
            self.assertRegexp('view', '1000.*2000')
            self.assertRegexp('view 1', '1000')
            self.assertRegexp('view nanotube', '1000.*2000')
            self.prefix = 'authedguy!stuff@123.345.234.34'
            self.assertNotError('otcorderbook buy 3000 btc at .7 eur')
            self.assertNotError('otcorderbook sell 4000 btc at .8 eur')
            self.assertRegexp('view 2', '2000')
            self.assertRegexp('view', '3000.*4000')
            self.assertRegexp('view nanotube', '1000.*2000')
            self.assertRegexp('view naNOtuBe', '1000.*2000')
        finally:
            self.prefix = origuser

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
