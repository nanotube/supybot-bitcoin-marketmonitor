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
import urllib2
import time
import traceback

opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0')]
urlopen = opener.open

def getNonNegativeFloat(irc, msg, args, state, type='floating point number'):
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

def getTo(irc, msg, args, state):
    if args[0].lower() in ['in', 'to']:
        args.pop(0)

addConverter('nonNegativeFloat', getNonNegativeFloat)
addConverter('currencyCode', getCurrencyCode)
addConverter('to', getTo)

class Market(callbacks.Plugin):
    """Add the help for "@plugin help Market" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Market, self)
        self.__parent.__init__(irc)
        self.lastdepthfetch = 0
        self.mdepth = None
        self.currency_cache = {}
        self.ticker_cache = {}

    def _queryYahooRate(self, cur1, cur2):
        try:
            cachedvalue = self.currency_cache[cur1+cur2]
            if time.time() - cachedvalue['time'] < 60:
                return cachedvalue['rate']
        except KeyError:
            pass
        queryurl = "http://query.yahooapis.com/v1/public/yql?q=select%%20*%%20from%%20yahoo.finance.xchange%%20where%%20pair=%%22%s%s%%22&env=store://datatables.org/alltableswithkeys&format=json"
        yahoorate = utils.web.getUrl(queryurl % (cur1, cur2,))
        yahoorate = json.loads(yahoorate, parse_float=str, parse_int=str)
        rate = yahoorate['query']['results']['rate']['Rate']
        if float(rate) == 0:
            raise ValueError, "no data"
        self.currency_cache[cur1 + cur2] = {'time':time.time(), 'rate':rate}
        return rate

    def _getMarketDepth(self):
        if world.testing: # avoid hammering mtgox api when testing.
            self.mdepth = json.load(open('/tmp/mtgox.depth.json'))['return']
            return
        try:
            if time.time() - self.lastdepthfetch > self.registryValue('fullDepthCachePeriod'): 
                data = urlopen('http://data.mtgox.com/api/1/BTCUSD/depth/full').read()
                self.mdepth = json.loads(data)
                self.mdepth = self.mdepth['return']
                self.mdepth['bids'].reverse() # bids are listed in ascending order
                self.lastdepthfetch = time.time()
        except:
            pass # oh well, try again later.

    def _getMtgoxTicker(self, currency):
        if world.testing and currency == 'USD':
            ticker = json.load(open('/tmp/mtgox.ticker.json'))
        else:
            try:
                cachedvalue = self.ticker_cache['mtgox'+currency]
                if time.time() - cachedvalue['time'] < 3:
                    return cachedvalue['ticker']
            except KeyError:
                pass
            stdticker = {}
            try:
                json_data = urlopen("https://data.mtgox.com/api/2/BTC%s/money/ticker" % (currency.upper(),)).read()
            except urllib2.HTTPError:
                json_data = '{"result":"error"}'
            try:
                ftj = urlopen("http://data.mtgox.com/api/2/BTC%s/money/ticker_fast" % (currency.upper(),)).read()
            except urllib2.HTTPError:
                ftj = '{"result":"error"}'
            ticker = json.loads(json_data)
            yahoorate = 1
            if ticker['result'] == 'error' and currency != 'USD':
                # maybe currency just doesn't exist, so try USD and convert.
                ticker = json.loads(urlopen("https://data.mtgox.com/api/2/BTCUSD/money/ticker").read())
                try:
                    stdticker = {'warning':'using yahoo currency conversion'}
                    yahoorate = float(self._queryYahooRate('USD', currency))
                except:
                    stdticker = {'error':'failed to get currency conversion from yahoo.'}
                    return stdticker
            tf = json.loads(ftj)
            if ticker['result'] != 'error' and tf['result'] != 'error': # use fast ticker where available
                ticker['data']['buy']['value'] = tf['data']['buy']['value']
                ticker['data']['sell']['value'] = tf['data']['sell']['value']
                ticker['data']['last']['value'] = tf['data']['last']['value']
        if ticker['result'] == 'error':
             stdticker = {'error':ticker['error']}
        else:
            stdticker.update({'bid': float(ticker['data']['buy']['value'])*yahoorate,
                                'ask': float(ticker['data']['sell']['value'])*yahoorate,
                                'last': float(ticker['data']['last']['value'])*yahoorate,
                                'vol': ticker['data']['vol']['value'],
                                'low': float(ticker['data']['low']['value'])*yahoorate,
                                'high': float(ticker['data']['high']['value'])*yahoorate,
                                'avg': float(ticker['data']['vwap']['value'])*yahoorate})
        self.ticker_cache['mtgox'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBtceTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['btce'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        if currency.lower() == 'ltc':
            pair = 'ltc_btc'
        else:
            pair = 'btc_%s' % (currency.lower(),)
        json_data = urlopen("https://btc-e.com/api/2/%s/ticker" % (pair,)).read()
        ticker = json.loads(json_data)
        yahoorate = 1
        if ticker.has_key('error'):
            # maybe we have unsupported currency
            ticker = json.loads(urlopen("https://btc-e.com/api/2/btc_usd/ticker").read())
            if ticker.has_key('error'):
                stdticker = {'error':ticker['error']}
                return stdticker
            try:
                stdticker = {'warning':'using yahoo currency conversion'}
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        ticker = ticker['ticker']
        if currency.lower() == 'ltc':
            stdticker = {'bid': round(1.0/ticker['buy'],6),
                            'ask': round(1.0/ticker['sell'],6),
                            'last': round(1.0/ticker['last'],6),
                            'vol': ticker['vol'],
                            'low': round(1.0/ticker['high'],6),
                            'high': round(1.0/ticker['low'],6),
                            'avg': round(1.0/ticker['avg'],6)}
        else:
            stdticker.update({'bid': float(ticker['sell'])*yahoorate,
                            'ask': float(ticker['buy'])*yahoorate,
                            'last': float(ticker['last'])*yahoorate,
                            'vol': ticker['vol_cur'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(ticker['avg'])*yahoorate})
        self.ticker_cache['btce'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBitstampTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bitstamp'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("https://www.bitstamp.net/api/ticker/").read()
        ticker = json.loads(json_data)
        bcharts = json.loads(urlopen("http://api.bitcoincharts.com/v1/markets.json").read())
        yahoorate = 1
        if currency != 'USD':
            try:
                stdticker = {'warning':'using yahoo currency conversion'}
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        bcharts = filter(lambda x: x['symbol'] == 'bitstampUSD', bcharts)[0]
        stdticker.update({'bid': float(ticker['bid'])*yahoorate,
                            'ask': float(ticker['ask'])*yahoorate,
                            'last': float(ticker['last'])*yahoorate,
                            'vol': ticker['volume'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(bcharts['avg'])*yahoorate})
        self.ticker_cache['bitstamp'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBitfinexTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bitfinex'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        if currency.lower() == 'ltc':
            pair = 'ltcbtc'
        else:
            pair = 'btc%s' % (currency.lower(),)
        json_data = urlopen("https://api.bitfinex.com/v1/ticker/%s" % (pair,)).read()
        spotticker = json.loads(json_data)
        json_data = urlopen("https://api.bitfinex.com/v1/today/%s" % (pair,)).read()
        dayticker = json.loads(json_data)
        if spotticker.has_key('message') or dayticker.has_key('message'):
            stdticker = {'error':spotticker.get('message') or dayticker.get('message')}
        else:
            if currency.lower() == 'ltc':
                stdticker = {'bid': round(1.0/float(spotticker['ask']),6),
                                'ask': round(1.0/float(spotticker['bid']),6),
                                'last': round(1.0/float(spotticker['last_price']),6),
                                'vol': dayticker['volume'],
                                'low': round(1.0/float(dayticker['high']),6),
                                'high': round(1.0/float(dayticker['low']),6),
                                'avg': None}
            else:
                stdticker = {'bid': spotticker['bid'],
                                'ask': spotticker['ask'],
                                'last': spotticker['last_price'],
                                'vol': dayticker['volume'],
                                'low': dayticker['low'],
                                'high': dayticker['high'],
                                'avg': None}
        self.ticker_cache['bitfinex'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBtcdeTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['btcde'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("http://api.bitcoincharts.com/v1/markets.json").read()
        ticker = json.loads(json_data)
        trades = urlopen('http://api.bitcoincharts.com/v1/trades.csv?symbol=btcdeEUR').readlines()
        last = float(trades[-1].split(',')[1])
        yahoorate = 1
        if currency != 'EUR':
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('EUR', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        ticker = filter(lambda x: x['symbol'] == 'btcdeEUR', ticker)[0]
        stdticker.update({'bid': float(ticker['bid'])*yahoorate,
                            'ask':float(ticker['ask'])*yahoorate,
                            'last': float(last)*yahoorate,
                            'vol': ticker['volume'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(ticker['avg'])*yahoorate})
        self.ticker_cache['btcde'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getCbxTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['campbx'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("http://api.bitcoincharts.com/v1/markets.json").read()
        ticker = json.loads(json_data)
        cbx = json.loads(urlopen('http://campbx.com/api/xticker.php').read())
        yahoorate = 1
        if currency != 'USD':
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        ticker = filter(lambda x: x['symbol'] == 'cbxUSD', ticker)[0]
        stdticker.update({'bid': float(cbx['Best Bid'])*yahoorate,
                            'ask': float(cbx['Best Ask'])*yahoorate,
                            'last': float(cbx['Last Trade'])*yahoorate,
                            'vol': ticker['volume'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(ticker['avg'])*yahoorate})
        self.ticker_cache['campbx'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBtcchinaTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['btcchina'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        try:
            json_data = urlopen("http://api.bitcoincharts.com/v1/markets.json").read()
            bcharts = json.loads(json_data)
        except:
            bcharts = [{'symbol':'btcnCNY','avg':None}]
        btcchina = json.loads(urlopen('https://data.btcchina.com/data/ticker').read())['ticker']
        yahoorate = 1
        if currency not in ['CNY', 'RMB']:
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('CNY', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        bcharts = filter(lambda x: x['symbol'] == 'btcnCNY', bcharts)[0]
        if bcharts['avg'] is not None:
            avg = float(bcharts['avg'])*yahoorate
        else:
            avg = None
        stdticker.update({'bid': float(btcchina['buy'])*yahoorate,
                            'ask': float(btcchina['sell'])*yahoorate,
                            'last': float(btcchina['last'])*yahoorate,
                            'vol': btcchina['vol'],
                            'low': float(btcchina['low'])*yahoorate,
                            'high': float(btcchina['high'])*yahoorate,
                            'avg': avg})
        self.ticker_cache['btcchina'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBitcoinaverageTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bitcoinaverage'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        try:
            ticker = json.loads(urlopen('https://api.bitcoinaverage.com/ticker/%s' % (currency,)).read())
        except urllib2.HTTPError:
            stdticker = {'error':'Unsupported currency.'}
            return stdticker
        except:
            stdticker = {'error':'Problem retrieving data.'}
            return stdticker
        stdticker = {'bid': float(ticker['bid']),
                            'ask': float(ticker['ask']),
                            'last': float(ticker['last']),
                            'vol': ticker['total_vol'],
                            'low': None,
                            'high': None,
                            'avg': float(ticker['24h_avg'])}
        self.ticker_cache['bitcoinaverage'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getCoinbaseTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['coinbase'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        try:
            last = json.loads(urlopen('https://coinbase.com/api/v1/prices/spot_rate').read())['amount']
            ask = json.loads(urlopen('https://coinbase.com/api/v1/prices/buy').read())['amount']
            bid = json.loads(urlopen('https://coinbase.com/api/v1/prices/sell').read())['amount']
        except:
            stdticker = {'error':'Problem retrieving data.'}
            return
        if currency != 'USD':
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        else:
            yahoorate = 1
        stdticker.update({'bid': float(bid)*yahoorate,
                            'ask': float(ask)*yahoorate,
                            'last': float(last)*yahoorate,
                            'vol': None,
                            'low': None,
                            'high': None,
                            'avg': None})
        self.ticker_cache['coinbase'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

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

    def baratio(self, irc, msg, args):
        """takes no arguments
        
        Calculate the ratio of total usd volume of bids to total btc volume of asks.
        """
        self._getMarketDepth()
        try:
            asks =self.mdepth['asks']
            bids = self.mdepth['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return

        totalasks = 0
        for ask in asks:
            totalasks += ask['amount']
        totalbids = 0
        for bid in bids:
            totalbids += bid['amount'] * bid['price']
        ratio = totalbids / totalasks
        irc.reply("Total bids: %d USD. Total asks: %d BTC. Ratio: %.5f USD/BTC."
                " | Data vintage: %.4f seconds"
                % (totalbids, totalasks, ratio, (time.time() - self.lastdepthfetch),))
    baratio = wrap(baratio)

    def premium(self, irc, msg, args, market1, market2):
        '''<market1> <market2>
        
        Calculate the premium of market1 over market2, using last trade price.
        Uses USD exchange rate. If USD is not traded on one of the target
        markets, queries currency conversion from google.
        '''
        supportedmarkets = {'mtgox':'MtGox','btce':'BTC-E', 'bitstamp':'Bitstamp',
                'bitfinex':'Bitfinex', 'btcde':'Bitcoin.de', 'cbx':'CampBX',
                'btcn':'BTCChina', 'coinbase':'Coinbase'}
        if market1 not in supportedmarkets.keys() or market2 not in supportedmarkets.keys():
            irc.error("This is not one of the supported markets. Please choose one of %s." % (supportedmarkets.keys(),))
            return
        dispatch = {'mtgox':self._getMtgoxTicker, 'btce':self._getBtceTicker,
                'bitstamp':self._getBitstampTicker, 'bitfinex': self._getBitfinexTicker,
                'btcde':self._getBtcdeTicker, 'cbx':self._getCbxTicker,
                'btcn':self._getBtcchinaTicker,'coinbase':self._getCoinbaseTicker}
        try:
            last1 = float(dispatch[market1]('USD')['last'])
            last2 = float(dispatch[market2]('USD')['last'])
        except:
                irc.error("Failure to retrieve ticker. Try again later.")
                return
        prem = (last1-last2)/last2*100
        irc.reply("Premium of %s over %s is currently %s %%." % \
                (supportedmarkets[market1], supportedmarkets[market2], prem,))
    premium = wrap(premium, ['something','something'])
    
    def ticker(self, irc, msg, args, optlist):
        """[--bid|--ask|--last|--high|--low|--avg|--vol] [--currency XXX] [--market <market>|all]
        
        Return pretty-printed ticker. Default market is Mtgox. 
        If one of the result options is given, returns only that numeric result
        (useful for nesting in calculations).
        
        If '--currency XXX' option  is given, returns ticker for that three-letter currency code.
        It is up to you to make sure the code is a valid currency on your target market.
        Default currency is USD.
        """
        supportedmarkets = {'mtgox':'MtGox','btce':'BTC-E', 'bitstamp':'Bitstamp',
                'bitfinex':'Bitfinex', 'btcde':'Bitcoin.de', 'cbx':'CampBX',
                'btcn':'BTCChina', 'btcavg':'BitcoinAverage', 'coinbase':'Coinbase',
                'all':'all'}
        od = dict(optlist)
        currency = od.pop('currency', 'USD')
        market = od.pop('market','mtgox').lower()
        if market not in supportedmarkets.keys():
            irc.error("This is not one of the supported markets. Please choose one of %s." % (supportedmarkets.keys(),))
            return
        if len(od) > 1:
            irc.error("Please only choose at most one result option at a time.")
            return
        dispatch = {'mtgox':self._getMtgoxTicker, 'btce':self._getBtceTicker,
                'bitstamp':self._getBitstampTicker, 'bitfinex': self._getBitfinexTicker,
                'btcde':self._getBtcdeTicker, 'cbx':self._getCbxTicker,
                'btcn':self._getBtcchinaTicker, 'btcavg':self._getBitcoinaverageTicker,
                'coinbase':self._getCoinbaseTicker}
        if market != 'all':
            try:
                ticker = dispatch[market](currency)
            except Exception, e:
                irc.error("Failure to retrieve ticker. Try again later.")
                self.log.info("Problem retrieving ticker. Market %s, Error: %s" %\
                            (market, e,))
                return
            if ticker.has_key('error'):
                irc.error('Error retrieving ticker. Details: %s' % (ticker['error'],))
                return

            if len(od) == 0:
                irc.reply("%s BTC%s ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, "
                    "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s" % \
                    (supportedmarkets[market], currency, ticker['bid'], ticker['ask'],
                    float(ticker['ask']) - float(ticker['bid']), ticker['last'],
                    ticker['vol'], ticker['low'], ticker['high'],
                    ticker['avg']))
            else:
                key = od.keys()[0]
                irc.reply(ticker[key])
        else:
            if currency != 'USD':
                irc.error('Only USD averages supported.')
                return
            response = ""
            sumvol = 0
            sumprc = 0
            for mkt in ['mtgox','bitstamp','btce','bitfinex','cbx','btcn']:
                try:
                    tck = dispatch[mkt](currency)
                    response += "%s BTCUSD last: %s, vol: %s | " % \
                            (supportedmarkets[mkt], tck['last'], tck['vol'])
                except:
                    continue # we'll just skip this one then
                sumvol += float(tck['vol'])
                sumprc += float(tck['vol']) * float(tck['last'])
            response += "Volume-weighted last average: %s" % (sumprc/sumvol,)
            irc.reply(response)
    ticker = wrap(ticker, [getopts({'bid': '','ask': '','last': '','high': '',
            'low': '', 'avg': '', 'vol': '', 'currency': 'currencyCode', 'market': 'something'})])

    def goxlag(self, irc, msg, args, optlist):
        """[--raw]
        
        Retrieve mtgox order processing lag. If --raw option is specified
        only output the raw number of seconds. Otherwise, dress it up."""
        try:
            json_data = urlopen("https://mtgox.com/api/2/money/order/lag").read()
            lag = json.loads(json_data)
            lag_secs = lag['data']['lag_secs']
        except:
            irc.error("Problem retrieving gox lag. Try again later.")
            return

        if dict(optlist).has_key('raw'):
            irc.reply("%s" % (lag_secs,))
            return
        
        result = "MtGox lag is %s seconds." % (lag_secs,)
        
        au = lag_secs / 499.004784
        meandistance = {0: "... nowhere, really",
                        0.0001339: "to the other side of the Earth, along the surface",
                        0.0024: "across the outer diameter of Saturn's rings",
                        0.00257: "from Earth to Moon",
                        0.002819: "from Jupiter to its third largest moon, Io",
                        0.007155: "from Jupiter to its largest moon, Ganymede",
                        0.00802: "from Saturn to its largest moon, Titan",
                        0.012567: "from Jupiter to its second largest moon, Callisto",
                        0.016: "one full loop along the orbit of the Moon around Earth",
                        0.0257: 'ten times between Earth and Moon',
                        0.0689: "approximately the distance covered by Voyager 1 in one week",
                        0.0802: "ten times between Saturn and Titan",
                        0.12567: "ten times between Jupiter and Callisto",
                        0.2540: 'between Earth and Venus at their closest approach',
                        0.257: 'one hundred times between Earth and Moon',
                        0.2988: 'approximately the distance covered by Voyager 1 in one month',
                        0.39: 'from the Sun to Mercury',
                        0.72: 'from the Sun to Venus',
                        1: 'from the Sun to Earth',
                        1.52: 'from the Sun to Mars',
                        2.77: 'from the Sun to Ceres (in the main asteroid belt)',
                        5.2: 'from the Sun to Jupiter',
                        9.54: 'from the Sun to Saturn',
                        19.18: 'from the Sun to Uranus',
                        30.06: 'from the Sun to Neptune',
                        39.44: 'from the Sun to Pluto (Kuiper belt)',
                        100: 'from the Sun to heliopause (out of the solar system!)'}
        import operator
        distances = meandistance.keys()
        diffs = map(lambda x: abs(operator.__sub__(x, au)), distances)
        bestdist = distances[diffs.index(min(diffs))]
        objectname = meandistance[bestdist]
        result += " During this time, light travels %s AU. You could have sent a bitcoin %s (%s AU)." % (au, objectname, bestdist)
        irc.reply(result)
    goxlag = wrap(goxlag, [getopts({'raw': ''})])

    def convert(self, irc, msg, args, amount, currency1, currency2):
        """[<amount>] <currency1> [to|in] <currency2>
        
        Convert <currency1> to <currency2> using Yahoo api.
        If optional <amount> is given, converts <amount> units of currency1.
        """
        if amount is None:
            amount = 1
        try:
            result = self._queryYahooRate(currency1, currency2)
            irc.reply(float(result)*amount)
        except:
            irc.error("Problem retrieving data.")
    convert = wrap(convert, [optional('nonNegativeFloat'), 'currencyCode', 'to', 'currencyCode'])

Class = Market


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
