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
from supybot import conf
from supybot import world

import re
import json
from urllib2 import urlopen
import time

def getNonNegativeFloat(irc, msg, args, state, type=' floating point number'):
    try:
        v = float(args[0])
        if v < 0:
            raise ValueError, "only non-negative numbers allowed."
        state.args.append(v)
        del args[0]
    except ValueError:
        state.errorInvalid(type, args[0])

def getCurrencyCode(irc, msg, args, state, type='currency code'):
    v = args[0]
    m = re.search(r'^([A-Za-z]{3})$', v)
    if m is None:
        state.errorInvalid(type, args[0])
        return
    state.args.append(m.group(1).upper())
    del args[0]

addConverter('nonNegativeFloat', getNonNegativeFloat)
addConverter('currencyCode', getCurrencyCode)

class Market(callbacks.Plugin):
    """Add the help for "@plugin help Market" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Market, self)
        self.__parent.__init__(irc)
        self.lastdepthfetch = 0
        self.mdepth = None

    def _getMarketDepth(self):
        if world.testing: # avoid hammering mtgox api when testing.
            self.mdepth = json.load(open('/tmp/mtgox.depth.json'))['return']
            return
        try:
            if time.time() - self.lastdepthfetch > 120: # don't fetch from gox more often than every 2 min
                data = urlopen('http://data.mtgox.com/api/1/BTCUSD/depth/full').read()
                self.mdepth = json.loads(data)
                self.mdepth = self.mdepth['return']
                self.mdepth['bids'].reverse() # bids are listed in ascending order
                self.lastdepthfetch = time.time()
        except:
            pass # oh well, try again later.

    def _getTicker(self, currency):
        json_data = urlopen("https://data.mtgox.com/api/1/BTC%s/ticker" % (currency.upper(),)).read()
        ticker = json.loads(json_data)
        return ticker

    def _sellbtc(self, bids, value):
        n_coins = value
        total = 0.0
        top = 0.0
        all = False
        for bid in bids:
            if n_coins <= bid['amount']: # we don't have enough
                total += n_coins * bid['price']
                top = bid['price']
                break
            else: # we can eat the entire order
                n_coins -= bid['amount']
                total += bid['amount'] * bid['price']
        else:
            all = True
        return({'n_coins':n_coins, 'total':total, 'top':top, 'all':all})

    def _sellusd(self, bids, value):
        n_coins = 0.0
        total = value
        top = 0.0
        all = False
        for bid in bids:
            if total <= bid['amount'] * bid['price']: 
                n_coins += total / bid['price']
                top = bid['price']
                break
            else: # we can eat the entire order
                n_coins += bid['amount']
                total -= bid['amount'] * bid['price']
        else:
            all = True
        return({'n_coins':n_coins, 'total':total, 'top':top, 'all':all})

    def sell(self, irc, msg, args, optlist, value):
        """[--usd] <value>
        
        Calculate the effect on the market depth of a market sell order of
        <value> bitcoins. If '--usd' option is given, <value> denotes the 
        size of the order in USD.
        """
        self._getMarketDepth()
        try:
            bids = self.mdepth['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        if dict(optlist).has_key('usd'):
            r = self._sellusd(bids, value)
            if r['all']:
                irc.reply("This order would exceed the size of the order book. "
                        "You would sell %.8g bitcoins for a total of %.4f USD and "
                        "take the price to 0."
                        " | Data vintage: %.4f seconds"
                        % (r['n_coins'], value - r['total'], (time.time() - self.lastdepthfetch),))
            else:
                irc.reply("A market order to sell %.4f USD worth of bitcoins right "
                        "now would sell %.8g bitcoins and would take the last "
                        "price down to %.4f USD, resulting in an average price of "
                        "%.4f USD/BTC."
                        " | Data vintage: %.4f seconds"
                        % (value, r['n_coins'], r['top'],(value/r['n_coins']), (time.time() - self.lastdepthfetch),))
        else:
            r = self._sellbtc(bids, value)
            if r['all']:
                irc.reply("This order would exceed the size of the order book. "
                        "You would sell %.8g bitcoins, for a total of %.4f USD and "
                        "take the price to 0."
                        " | Data vintage: %.4f seconds"
                        % (value - r['n_coins'], r['total'], (time.time() - self.lastdepthfetch),))
            else:
                irc.reply("A market order to sell %.8g bitcoins right now would "
                        "net %.4f USD and would take the last price down to %.4f USD, "
                        "resulting in an average price of %.4f USD/BTC."
                        " | Data vintage: %.4f seconds"
                        % (value, r['total'], r['top'], (r['total']/value), (time.time() - self.lastdepthfetch)))
    sell = wrap(sell, [getopts({'usd': '',}), 'nonNegativeFloat'])

    def _buybtc(self, asks, value):
        n_coins = value
        total = 0.0
        top = 0.0
        all = False
        for ask in asks:
            if n_coins <= ask['amount']: # we don't have enough
                total += n_coins * ask['price']
                top = ask['price']
                break
            else: # we can eat the entire order
                n_coins -= ask['amount']
                total += ask['amount'] * ask['price']
                top = ask['price']
        else:
            all = True
        return({'n_coins':n_coins, 'total':total, 'top':top, 'all':all})

    def _buyusd(self, asks, value):
        n_coins = 0.0
        total = value
        top = 0.0
        all = False
        for ask in asks:
            if total <= ask['amount'] * ask['price']: 
                n_coins += total / ask['price']
                top = ask['price']
                break
            else: # we can eat the entire order
                n_coins += ask['amount']
                total -= ask['amount'] * ask['price']
                top = ask['price']
        else:
            all = True
        return({'n_coins':n_coins, 'total':total, 'top':top, 'all':all})

    def buy(self, irc, msg, args, optlist, value):
        """[--usd] <value>
        
        Calculate the effect on the market depth of a market buy order of
        <value> bitcoins. If '--usd' option is given, <value> denotes the 
        size of the order in USD.
        """
        self._getMarketDepth()
        try:
            asks =self.mdepth['asks']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        if dict(optlist).has_key('usd'):
            r = self._buyusd(asks, value)
            if r['all']:
                irc.reply("This order would exceed the size of the order book. "
                        "You would buy %.8g bitcoins for a total of %.4f USD and "
                        "take the price to %.4f."
                        " | Data vintage: %.4f seconds"
                        % (r['n_coins'], value - r['total'], r['top'], (time.time() - self.lastdepthfetch),))
            else:
                irc.reply("A market order to buy %.4f USD worth of bitcoins right "
                        "now would buy %.8g bitcoins and would take the last "
                        "price up to %.4f USD, resulting in an average price of "
                        "%.4f USD/BTC."
                        " | Data vintage: %.4f seconds"
                        % (value, r['n_coins'], r['top'],(value/r['n_coins']), (time.time() - self.lastdepthfetch),))
        else:
            r = self._buybtc(asks, value)
            if r['all']:
                irc.reply("This order would exceed the size of the order book. "
                        "You would buy %.8g bitcoins, for a total of %.4f USD and "
                        "take the price to %.4f."
                        " | Data vintage: %.4f seconds"
                        % (value - r['n_coins'], r['total'], r['top'], (time.time() - self.lastdepthfetch),))
            else:
                irc.reply("A market order to buy %.8g bitcoins right now would "
                        "take %.4f USD and would take the last price up to %.4f USD, "
                        "resulting in an average price of %.4f USD/BTC."
                        " | Data vintage: %.4f seconds"
                        % (value, r['total'], r['top'], (r['total']/value), (time.time() - self.lastdepthfetch),))
    buy = wrap(buy, [getopts({'usd': '',}), 'nonNegativeFloat'])


    def asks(self, irc, msg, args, optlist, pricetarget):
        """[--over] <pricetarget>
        
        Calculate the amount of bitcoins for sale at or under <pricetarget>.
        If '--over' option is given, find coins or at or over <pricetarget>.
        """
        self._getMarketDepth()
        response = "under"
        if dict(optlist).has_key('over'):
            f = lambda price,pricetarget: price >= pricetarget
            response = "over"
        else:
            f = lambda price,pricetarget: price <= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            asks =self.mdepth['asks']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        for ask in asks:
            if f(ask['price'], pricetarget):
                n_coins += ask['amount']
                total += (ask['amount'] * ask['price'])

        irc.reply("There are currently %.8g bitcoins offered at "
                "or %s %s USD, worth %s USD in total."
                " | Data vintage: %.4f seconds"
                % (n_coins, response, pricetarget, total, (time.time() - self.lastdepthfetch),))
    asks = wrap(asks, [getopts({'over': '',}), 'nonNegativeFloat'])

    def bids(self, irc, msg, args, optlist, pricetarget):
        """[--under] <pricetarget>
        
        Calculate the amount of bitcoin demanded at or over <pricetarget>.
        If '--under' option is given, find coins or at or under <pricetarget>.
        """
        self._getMarketDepth()
        response = "over"
        if dict(optlist).has_key('under'):
            f = lambda price,pricetarget: price <= pricetarget
            response = "under"
        else:
            f = lambda price,pricetarget: price >= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            bids =self.mdepth['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        for bid in bids:
            if f(bid['price'], pricetarget):
                n_coins += bid['amount']
                total += (bid['amount'] * bid['price'])

        irc.reply("There are currently %.8g bitcoins demanded at "
                "or %s %s USD, worth %s USD in total."
                " | Data vintage: %.4f seconds"
                % (n_coins, response, pricetarget, total, (time.time() - self.lastdepthfetch),))
    bids = wrap(bids, [getopts({'under': '',}), 'nonNegativeFloat'])

    def obip(self, irc, msg, args, width):
        """<width>
        
        Calculate the "order book implied price", by finding the weighted
        average price of coins <width> BTC up and down from the spread.
        """
        self._getMarketDepth()
        try:
            asks =self.mdepth['asks']
            bids = self.mdepth['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return

        b = self._buybtc(asks, width)
        s = self._sellbtc(bids, width)
        if b['all'] or s['all']:
            irc.error("The width provided extends past the edge of the order book. Please use a smaller width.")
            return
        obip = (b['total'] + s['total'])/2.0/width
        irc.reply("The weighted average price of BTC, %s coins up and down from the spread, is %.5f USD."
                " | Data vintage: %.4f seconds"
                % (width, obip,(time.time() - self.lastdepthfetch),))
    obip = wrap(obip, ['nonNegativeFloat'])

    def ticker(self, irc, msg, args, optlist):
        """[--bid|--ask|--last|--high|--low|--avg] [--currency XXX]
        
        Return pretty-printed mtgox ticker. 
        If one of the result options is given, returns only that numeric result
        (useful for nesting in calculations).
        
        If '--currency XXX' option  is given, returns ticker for that three-letter currency code.
        It is up to you to make sure that the three letter code you enter is a valid currency
        that is traded on mtgox. Default currency is USD.
        """
        od = dict(optlist)
        if ('currency' not in od.keys() and len(od) > 1) or ('currency' in od.keys() and len(od) > 2):
            irc.error("Please only choose at most one result option at a time.")
            return
        currency = od.pop('currency', 'USD')
        try:
            ticker = self._getTicker(currency)
        except:
            irc.error("Failure to retrieve ticker. Try again later.")
            return
        if ticker['result'] == 'error':
            irc.error('Error retrieving ticker. Details: %s' % (ticker['error'],))
            return

        if len(od) == 0:
            irc.reply("BTC%s ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, "
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s" % \
                (currency, ticker['return']['buy']['value'], ticker['return']['sell']['value'],
                float(ticker['return']['sell']['value']) - float(ticker['return']['buy']['value']),
                ticker['return']['last']['value'], ticker['return']['vol']['value'],
                ticker['return']['low']['value'], ticker['return']['high']['value'],
                ticker['return']['vwap']['value']))
        else:
            key = od.keys()[0]
            key = {'bid':'buy', 'ask':'sell', 'avg':'vwap'}.setdefault(key, key)
            irc.reply(ticker['return'][key]['value'])
    ticker = wrap(ticker, [getopts({'bid': '','ask': '','last': '','high': '',
            'low': '', 'avg': '', 'currency': 'currencyCode'})])

Class = Market


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
