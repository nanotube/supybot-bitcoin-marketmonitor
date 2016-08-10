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
import supybot.callbacks as callbacks
from supybot import world
from supybot.utils.seq import dameraulevenshtein

import re
import json
import urllib2
import time
import traceback
import inspect

opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0')]
urlopen = opener.open

def getNonNegativeFloat(irc, msg, args, state, type='non-negative floating point number'):
    try:
        v = float(args[0])
        if v < 0:
            raise ValueError, "only non-negative numbers allowed."
        state.args.append(v)
        del args[0]
    except ValueError:
        state.errorInvalid(type, args[0])

def getPositiveFloat(irc, msg, args, state, type='positive floating point number'):
    try:
        v = float(args[0])
        if v <= 0:
            raise ValueError, "only positive numbers allowed."
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
addConverter('positiveFloat', getPositiveFloat)
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
        self.depth_cache = {}
        self.currency_cache = {}
        self.ticker_cache = {}
        self.ticker_supported_markets = {
            'bcent': 'Bitcoin-Central',
            'bfx': 'Bitfinex',
            'bitmynt': 'bitmynt.no',
            'btcavg': 'BitcoinAverage',
            'btcde': 'Bitcoin.de',
            'btce': 'BTC-E',
            'btcn': 'BTCChina',
            'btsp': 'Bitstamp',
            'cbx': 'CampBX',
            'coinbase': 'Coinbase',
            'gdax': 'GDAX',
            'gem': 'Gemini',
            'krk': 'Kraken',
            'okc': 'OKCoin'
        }
        self.depth_supported_markets = {
            'bcent': 'Bitcoin-Central',
            'btce': 'BTC-E',
            'btcn': 'BTCChina',
            'btsp': 'Bitstamp',
            'bfx': 'Bitfinex',
            'gdax': 'GDAX',
            'gem': 'Gemini',
            'krk': 'Kraken'
        }
        
        self._parseMarketDocstrings()
        
    def _parseMarketDocstrings(self):
        attrs = inspect.getmembers(self, predicate=inspect.ismethod)
        attrs = filter(lambda x: x[0][0] != '_' and x[1].__func__.__doc__ is not None, attrs)
        attrs = filter(lambda x: re.search('%market%', x[1].__func__.__doc__), attrs)
        def _changedoc(x):
            x[1].__func__.__doc__ = re.sub("%market%", self.ticker_supported_markets[self.registryValue('defaultExchange')], x[1].__func__.__doc__)
        map(_changedoc, attrs)

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

    def _getMtgoxDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            self.depth_cache['mtgox'] = {'time':time.time(), 
                    'depth':json.load(open('/tmp/mtgox.depth.json'))['return']}
            self.depth_cache['mtgox']['depth']['bids'].reverse()
            return
        try:
            cachedvalue = self.depth_cache['mtgox']
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        try:
            data = urlopen('http://data.mtgox.com/api/1/BTCUSD/depth/full').read()
            vintage = time.time()
            depth = json.loads(data)['return']
            depth['bids'].reverse() # bids should be listed in descending order
            self.depth_cache['mtgox'] = {'time':vintage, 'depth':depth}
        except:
            pass # oh well, try again later.

    def _getBtspDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/bitstamp.depth.json'))
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['btsp'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['btsp'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        if currency != 'USD':
            yahoorate = float(self._queryYahooRate('USD', currency))
        try:
            stddepth = {}
            data = urlopen('https://www.bitstamp.net/api/order_book/').read()
            vintage = time.time()
            depth = json.loads(data)
            # make consistent format with mtgox
            depth['bids'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['btsp'+currency] = {'time':vintage, 'depth':depth}
        except:
            pass # oh well, try again later.

    def _getKrkDepth(self, currency='EUR'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/kraken.depth.json'))
            depth = depth['result'][depth['result'].keys()[0]]
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['krk'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['krk'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            data = urlopen('https://api.kraken.com/0/public/Depth?pair=XBT%s' % (currency,)).read()
            depth = json.loads(data)
            vintage = time.time()
            if len(depth['error']) != 0:
                if "Unknown asset pair" in depth['error'][0]:
                    # looks like we have unsupported currency, default to EUR
                    depth = json.loads(urlopen("https://api.kraken.com/0/public/Depth?pair=XBTEUR").read())
                    if len(depth['error']) != 0:
                        return # oh well try again later
                    try:
                        stddepth = {'warning':'using yahoo currency conversion'}
                        yahoorate = float(self._queryYahooRate('EUR', currency))
                    except:
                        return # oh well try again later
                else:
                    return
            depth = depth['result'][depth['result'].keys()[0]]
            # make consistent format with mtgox
            stddepth.update({'bids': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']],
                    'asks': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]})
            self.depth_cache['krk'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            pass # oh well, try again later.

    def _getBfxDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/bfx.depth.json'))
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['bfx'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['bfx'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            data = urlopen('https://api.bitfinex.com/v1/book/BTCUSD').read()
            depth = json.loads(data)
            vintage = time.time()
            if depth.has_key('message'):
                return # looks like an error, try again later
            if currency != 'USD':
                try:
                    stddepth = {'warning':'using yahoo currency conversion'}
                    yahoorate = float(self._queryYahooRate('USD', currency))
                except:
                    return # guess yahoo is failing
            # make consistent format with mtgox
            stddepth.update({'bids': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['bids']],
                    'asks': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['asks']]})
            self.depth_cache['bfx'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            traceback.print_exc()
            pass # oh well, try again later.

    def _getBtceDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/btce.depth.json'))
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['btce'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['btce'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            data = urlopen('https://btc-e.com/api/2/btc_%s/depth' % (currency.lower(),)).read()
            depth = json.loads(data)
            vintage = time.time()
            if depth.has_key('error'):
                if "invalid pair" in depth['error']:
                    # looks like we have unsupported currency, default to EUR
                    depth = json.loads(urlopen("https://btc-e.com/api/2/btc_usd/depth").read())
                    if depth.has_key('error'):
                        return # oh well try again later
                    try:
                        stddepth = {'warning':'using yahoo currency conversion'}
                        yahoorate = float(self._queryYahooRate('USD', currency))
                    except:
                        return # oh well try again later
                else:
                    return
            # make consistent format with mtgox
            stddepth.update({'bids': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']],
                    'asks': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]})
            self.depth_cache['btce'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            pass # oh well, try again later.

    def _getBcentDepth(self, currency='EUR'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/bcent.depth.json'))
            depth['bids'] = [{'price':float(b['price']), 'amount':float(b['amount'])} for b in depth['bids']]
            depth['bids'].reverse() # want bids in descending order
            depth['asks'] = [{'price':float(b['price']), 'amount':float(b['amount'])} for b in depth['asks']]
            self.depth_cache['bcent'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['bcent'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            data = urlopen('https://paymium.com/api/v1/data/eur/depth').read()
            depth = json.loads(data)
            vintage = time.time()
            if currency != 'EUR':
                yahoorate = float(self._queryYahooRate('EUR', currency))
            if depth.has_key('errors'):
                return
            # make consistent format with mtgox
            stddepth.update({'bids': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['bids']],
                    'asks': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['asks']]})
            stddepth['bids'].reverse()
            self.depth_cache['bcent'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            pass # oh well, try again later.

    def _getBtcnDepth(self, currency='CNY'):
        yahoorate = 1
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/btcchina.depth.json'))
            depth['bids'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]
            depth['asks'].reverse() # asks should be listed in ascending order
            self.depth_cache['btcn'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['btcn'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        if currency != 'CNY':
            yahoorate = float(self._queryYahooRate('CNY', currency))
        try:
            data = urlopen('https://data.btcchina.com/data/orderbook').read()
            vintage = time.time()
            depth = json.loads(data)
            # make consistent format with mtgox
            depth['bids'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]
            depth['asks'].reverse() # asks should be listed in ascending order
            self.depth_cache['btcn'+currency] = {'time':vintage, 'depth':depth}
        except:
            pass # oh well, try again later.

    def _getGemDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/gem.depth.json'))
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['gem'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['gem'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            depth = json.load(urlopen('https://api.gemini.com/v1/book/BTCUSD'))
            vintage = time.time()
            if 'message' in depth:
                return # looks like an error, try again later
            if currency != 'USD':
                try:
                    stddepth['warning'] = "using yahoo currency conversion"
                    yahoorate = float(self._queryYahooRate('USD', currency))
                except:
                    return # guess yahoo is failing
            # make consistent format with mtgox original format
            stddepth.update({
                'bids': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['bids']],
                'asks': [{'price':float(b['price'])*yahoorate, 'amount':float(b['amount'])} for b in depth['asks']]
            })
            self.depth_cache['gem'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            traceback.print_exc()
            pass # oh well, try again later.

    def _getGdaxDepth(self, currency='USD'):
        if world.testing: # avoid hammering api when testing.
            depth = json.load(open('/tmp/gdax.depth.json'))
            depth['bids'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['bids']]
            depth['asks'] = [{'price':float(b[0]), 'amount':float(b[1])} for b in depth['asks']]
            self.depth_cache['gdax'+currency] = {'time':time.time(), 'depth':depth}
            return
        try:
            cachedvalue = self.depth_cache['gdax'+currency]
            if time.time() - cachedvalue['time'] < self.registryValue('fullDepthCachePeriod'):
                return
        except KeyError:
            pass
        yahoorate = 1
        try:
            stddepth = {}
            depth = json.load(urlopen('https://api.gdax.com//products/BTC-USD/book?level=3'))
            vintage = time.time()
            if 'message' in depth:
                return # looks like an error, try again later
            if currency != 'USD':
                try:
                    stddepth['warning'] = "using yahoo currency conversion"
                    yahoorate = float(self._queryYahooRate('USD', currency))
                except:
                    return # guess yahoo is failing
            # make consistent format with mtgox original format
            stddepth.update({
                'bids': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['bids']],
                'asks': [{'price':float(b[0])*yahoorate, 'amount':float(b[1])} for b in depth['asks']]
            })
            self.depth_cache['gdax'+currency] = {'time':vintage, 'depth':stddepth}
        except:
            traceback.print_exc()
            pass # oh well, try again later.

    def _getMtgoxTicker(self, currency):
        stdticker = {}
        yahoorate = 1
        if world.testing and currency == 'USD':
            ticker = json.load(open('/tmp/mtgox.ticker.json'))
        else:
            try:
                cachedvalue = self.ticker_cache['mtgox'+currency]
                if time.time() - cachedvalue['time'] < 3:
                    return cachedvalue['ticker']
            except KeyError:
                pass
            try:
                json_data = urlopen("https://data.mtgox.com/api/2/BTC%s/money/ticker" % (currency.upper(),)).read()
                ticker = json.loads(json_data)
            except Exception, e:
                ticker = {"result":"error", "error":e}
            try:
                ftj = urlopen("https://data.mtgox.com/api/2/BTC%s/money/ticker_fast" % (currency.upper(),)).read()
                tf = json.loads(ftj)
            except Exception, e:
                tf = {"result":"error", "error":e}
            if ticker['result'] == 'error' and currency != 'USD':
                # maybe currency just doesn't exist, so try USD and convert.
                ticker = json.loads(urlopen("https://data.mtgox.com/api/2/BTCUSD/money/ticker").read())
                try:
                    stdticker = {'warning':'using yahoo currency conversion'}
                    yahoorate = float(self._queryYahooRate('USD', currency))
                except:
                    stdticker = {'error':'failed to get currency conversion from yahoo.'}
                    return stdticker
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
        if currency.lower() in ['ltc', 'nmc']:
            pair = '%s_btc' % (currency.lower(),)
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
        if currency.lower() in ['ltc', 'nmc']:
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

    def _getBtspTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bitstamp'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("https://www.bitstamp.net/api/ticker/").read()
        ticker = json.loads(json_data)
        try:
            bcharts = json.loads(urlopen("http://api.bitcoincharts.com/v1/markets.json").read())
            bcharts = filter(lambda x: x['symbol'] == 'bitstampUSD', bcharts)[0]
            avg = float(bcharts['avg'])
        except:
            avg = 0
        yahoorate = 1
        if currency != 'USD':
            try:
                stdticker = {'warning':'using yahoo currency conversion'}
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        stdticker.update({'bid': float(ticker['bid'])*yahoorate,
                            'ask': float(ticker['ask'])*yahoorate,
                            'last': float(ticker['last'])*yahoorate,
                            'vol': ticker['volume'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': avg*yahoorate})
        self.ticker_cache['bitstamp'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getKrkTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['krk'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("https://api.kraken.com/0/public/Ticker?pair=XBT%s" % (currency,)).read()
        ticker = json.loads(json_data)
        yahoorate = 1
        if len(ticker['error']) != 0:
            if "Unknown asset pair" in ticker['error'][0]:
                # looks like we have unsupported currency
                ticker = json.loads(urlopen("https://api.kraken.com/0/public/Ticker?pair=XBTEUR").read())
                if len(ticker['error']) != 0:
                    stdticker = {'error':ticker['error']}
                    return stdticker
                try:
                    stdticker = {'warning':'using yahoo currency conversion'}
                    yahoorate = float(self._queryYahooRate('EUR', currency))
                except:
                    stdticker = {'error':'failed to get currency conversion from yahoo.'}
                    return stdticker
            else:
                stdticker = {'error':ticker['error']}
                return stdticker
        ticker = ticker['result'][ticker['result'].keys()[0]]
        stdticker.update({'bid': float(ticker['b'][0])*yahoorate,
                            'ask': float(ticker['a'][0])*yahoorate,
                            'last': float(ticker['c'][0])*yahoorate,
                            'vol': float(ticker['v'][1]),
                            'low': float(ticker['l'][1])*yahoorate,
                            'high': float(ticker['h'][1])*yahoorate,
                            'avg': float(ticker['p'][1])*yahoorate})
        self.ticker_cache['krk'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBcentTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bcent'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("https://paymium.com/api/v1/data/eur/ticker").read()
        ticker = json.loads(json_data)
        if ticker.has_key('errors'):
            stdticker = {'error':ticker['errors']}
            return stdticker
        yahoorate = 1
        if currency != 'EUR':
            try:
                stdticker = {'warning':'using yahoo currency conversion'}
                yahoorate = float(self._queryYahooRate('EUR', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        stdticker.update({'bid': float(ticker['bid'])*yahoorate,
                            'ask': float(ticker['ask'])*yahoorate,
                            'last': float(ticker['price'])*yahoorate,
                            'vol': float(ticker['volume']),
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(ticker['vwap'])*yahoorate})
        self.ticker_cache['bcent'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getOkcTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['okc'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        json_data = urlopen("https://www.okcoin.cn/api/ticker.do?symbol=btc_cny").read()
        ticker = json.loads(json_data)['ticker']
        yahoorate = 1
        if currency != 'CNY':
            try:
                stdticker = {'warning':'using yahoo currency conversion'}
                yahoorate = float(self._queryYahooRate('CNY', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        stdticker.update({'bid': float(ticker['buy'])*yahoorate,
                            'ask': float(ticker['sell'])*yahoorate,
                            'last': float(ticker['last'])*yahoorate,
                            'vol': float(ticker['vol']),
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': None})
        self.ticker_cache['okc'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBfxTicker(self, currency):
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
        json_data = urlopen("https://api.bitfinex.com/v1/pubticker/%s" % (pair,)).read()
        ticker = json.loads(json_data)
        if ticker.has_key('message'):
            stdticker = {'error':ticker.get('message')}
        else:
            if currency.lower() == 'ltc':
                stdticker = {'bid': round(1.0/float(ticker['ask']),6),
                                'ask': round(1.0/float(ticker['bid']),6),
                                'last': round(1.0/float(ticker['last_price']),6),
                                'vol': ticker['volume'],
                                'low': round(1.0/float(ticker['high']),6),
                                'high': round(1.0/float(ticker['low']),6),
                                'avg': None}
            else:
                stdticker = {'bid': ticker['bid'],
                                'ask': ticker['ask'],
                                'last': ticker['last_price'],
                                'vol': ticker['volume'],
                                'low': ticker['low'],
                                'high': ticker['high'],
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
        try:
            json_data = urlopen("http://api.bitcoincharts.com/v1/markets.json").read()
            ticker = json.loads(json_data)
            ticker = filter(lambda x: x['symbol'] == 'cbxUSD', ticker)[0]
        except:
            ticker = {'low':0, 'high':0, 'volume':0, 'avg':0}
        cbx = json.loads(urlopen('http://campbx.com/api/xticker.php').read())
        yahoorate = 1
        if currency != 'USD':
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        stdticker.update({'bid': float(cbx['Best Bid'])*yahoorate,
                            'ask': float(cbx['Best Ask'])*yahoorate,
                            'last': float(cbx['Last Trade'])*yahoorate,
                            'vol': ticker['volume'],
                            'low': float(ticker['low'])*yahoorate,
                            'high': float(ticker['high'])*yahoorate,
                            'avg': float(ticker['avg'])*yahoorate})
        self.ticker_cache['campbx'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBtcnTicker(self, currency):
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

    def _getBtcavgTicker(self, currency):
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
            raise # will get caught later
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

    def _getGemTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['gem'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}

        if currency.lower() == 'usd':
            yahoorate = 1
        else:
            stdticker['warning'] = {'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                return {'error':'failed to get currency conversion from yahoo.'}
        
        ticker = json.loads(urlopen('https://api.gemini.com/v1/pubticker/BTCUSD').read())

        if 'message' in ticker:
            stdticker['error'] = ticker.get('message')
        else:
            stdticker['bid'] = float(ticker['bid']) * yahoorate
            stdticker['ask'] = float(ticker['ask']) * yahoorate
            stdticker['last'] = float(ticker['last']) * yahoorate
            stdticker['vol'] = float(ticker['volume']['BTC'])
            stdticker['avg'] = float(ticker['volume']['USD']) / float(ticker['volume']['BTC']) * yahoorate
            stdticker['low'] = None
            stdticker['high'] = None

        self.ticker_cache['gem'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getGdaxTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['gdax'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}

        if currency.lower() == 'usd':
            yahoorate = 1
        else:
            stdticker['warning'] = {'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('USD', currency))
            except:
                return {'error':'failed to get currency conversion from yahoo.'}
        
        ticker = json.loads(urlopen('https://api.gdax.com/products/BTC-USD/ticker').read())
        stats = json.loads(urlopen('https://api.gdax.com/products/BTC-USD/stats').read())
        
        if 'message' in ticker or 'message' in stats:
            stdticker['error'] = ticker.get('message', 'no ticker error') + stats.get('message' + 'no stats error')
        else:
            stdticker['bid'] = float(ticker['bid']) * yahoorate
            stdticker['ask'] = float(ticker['ask']) * yahoorate
            stdticker['last'] = float(ticker['price']) * yahoorate
            stdticker['vol'] = float(ticker['volume'])
            stdticker['avg'] = None
            stdticker['low'] = float(stats['low']) * yahoorate
            stdticker['high'] = float(stats['high']) * yahoorate

        self.ticker_cache['gdax'+currency] = {'time':time.time(), 'ticker':stdticker}
        return stdticker

    def _getBitmyntTicker(self, currency):
        try:
            cachedvalue = self.ticker_cache['bitmynt'+currency]
            if time.time() - cachedvalue['time'] < 3:
                return cachedvalue['ticker']
        except KeyError:
            pass
        stdticker = {}
        yahoorate = 1
        if currency in ['EUR','NOK']:
            ticker = json.loads(urlopen("http://bitmynt.no/ticker-%s.pl" % (currency.lower(),)).read())
            ticker = ticker[currency.lower()]
        else:
            ticker = json.loads(urlopen("http://bitmynt.no/ticker-eur.pl").read())
            ticker = ticker['eur']
            stdticker = {'warning':'using yahoo currency conversion'}
            try:
                yahoorate = float(self._queryYahooRate('EUR', currency))
            except:
                stdticker = {'error':'failed to get currency conversion from yahoo.'}
                return stdticker
        stdticker.update({'bid': float(ticker['buy'])*yahoorate,
                            'ask': float(ticker['sell'])*yahoorate,
                            'last': (float(ticker['buy']) + float(ticker['sell']))/2*yahoorate,
                            'vol': None,
                            'low': None,
                            'high': None,
                            'avg': None})
        self.ticker_cache['bitmynt'+currency] = {'time':time.time(), 'ticker':stdticker}
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
        """[--fiat] [--market <market>] [--currency XXX] <value>
        
        Calculate the effect on the market depth of a market sell order of
        <value> bitcoins. 
        If <market> is provided, uses that exchange. Default is %market%.
        If --currency XXX is provided, converts to that fiat currency. Default is USD.
        If '--fiat' option is given, <value> denotes the size of the order in fiat.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency','USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        cachename = m[0]+currency
        try:
            bids = self.depth_cache[cachename]['depth']['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            traceback.print_exc()
            return
        if od.has_key('fiat'):
            r = self._sellusd(bids, value)
            if r['all']:
                irc.reply("%s | This order would exceed the size of the order book. "
                        "You would sell %.8g bitcoins for a total of %.4f %s and "
                        "take the price to 0."
                        " | Data vintage: %.4f seconds"
                        % (m[1], r['n_coins'], value - r['total'], currency, (time.time() - self.depth_cache[cachename]['time']),))
            else:
                irc.reply("%s | A market order to sell %.4f %s worth of bitcoins right "
                        "now would sell %.8g bitcoins and would take the last "
                        "price down to %.4f %s, resulting in an average price of "
                        "%.4f %s/BTC."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value, currency, r['n_coins'], r['top'], currency,
                        (value/r['n_coins']), currency, (time.time() - self.depth_cache[cachename]['time']),))
        else:
            r = self._sellbtc(bids, value)
            if r['all']:
                irc.reply("%s | This order would exceed the size of the order book. "
                        "You would sell %.8g bitcoins, for a total of %.4f %s and "
                        "take the price to 0."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value - r['n_coins'], r['total'], currency, (time.time() - self.depth_cache[cachename]['time']),))
            else:
                irc.reply("%s | A market order to sell %.8g bitcoins right now would "
                        "net %.4f %s and would take the last price down to %.4f %s, "
                        "resulting in an average price of %.4f %s/BTC."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value, r['total'], currency, r['top'], currency,
                        (r['total']/value), currency, (time.time() - self.depth_cache[cachename]['time'])))
    sell = wrap(sell, [getopts({'fiat':'', 'market':'something', 'currency': 'currencyCode'}), 'nonNegativeFloat'])

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
        """[--fiat] [--market <market>] [--currency XXX] <value>
        
        Calculate the effect on the market depth of a market buy order of
        <value> bitcoins. 
        If <market> is provided, uses that exchange. Default is %market%.
        If --currency XXX is provided, converts to that fiat currency. Default is USD.
        If '--fiat' option is given, <value> denotes the size of the order in fiat.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency','USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        cachename = m[0]+currency
        try:
            asks = self.depth_cache[cachename]['depth']['asks']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        if dict(optlist).has_key('fiat'):
            r = self._buyusd(asks, value)
            if r['all']:
                irc.reply("%s | This order would exceed the size of the order book. "
                        "You would buy %.8g bitcoins for a total of %.4f %s and "
                        "take the price to %.4f."
                        " | Data vintage: %.4f seconds"
                        % (m[1], r['n_coins'], value - r['total'], currency,
                        r['top'], (time.time() - self.depth_cache[cachename]['time']),))
            else:
                irc.reply("%s | A market order to buy %.4f %s worth of bitcoins right "
                        "now would buy %.8g bitcoins and would take the last "
                        "price up to %.4f %s, resulting in an average price of "
                        "%.4f %s/BTC."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value, currency, r['n_coins'], r['top'], currency,
                        (value/r['n_coins']), currency, (time.time() - self.depth_cache[cachename]['time']),))
        else:
            r = self._buybtc(asks, value)
            if r['all']:
                irc.reply("%s | This order would exceed the size of the order book. "
                        "You would buy %.8g bitcoins, for a total of %.4f %s and "
                        "take the price to %.4f."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value - r['n_coins'], r['total'], currency, r['top'],
                        (time.time() - self.depth_cache[cachename]['time']),))
            else:
                irc.reply("%s | A market order to buy %.8g bitcoins right now would "
                        "take %.4f %s and would take the last price up to %.4f %s, "
                        "resulting in an average price of %.4f %s/BTC."
                        " | Data vintage: %.4f seconds"
                        % (m[1], value, r['total'], currency, r['top'], currency,
                        (r['total']/value), currency, (time.time() - self.depth_cache[cachename]['time']),))
    buy = wrap(buy, [getopts({'fiat':'', 'market':'something', 'currency': 'currencyCode'}), 'nonNegativeFloat'])

    def asks(self, irc, msg, args, optlist, pricetarget):
        """[--over] [--market <market>] [--currency XXX] <pricetarget>
        
        Calculate the amount of bitcoins for sale at or under <pricetarget>.
        If '--over' option is given, find coins or at or over <pricetarget>.
        If market is supplied, uses that exchange. Default is %market%.
        If --currency XXX is provided, converts to that fiat currency. Default is USD.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency','USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        cachename = m[0]+currency
        response = "under"
        if dict(optlist).has_key('over'):
            f = lambda price,pricetarget: price >= pricetarget
            response = "over"
        else:
            f = lambda price,pricetarget: price <= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            asks = self.depth_cache[cachename]['depth']['asks']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        for ask in asks:
            if f(ask['price'], pricetarget):
                n_coins += ask['amount']
                total += (ask['amount'] * ask['price'])

        irc.reply("%s | There are currently %.8g bitcoins offered at "
                "or %s %s %s, worth %s %s in total."
                " | Data vintage: %.4f seconds"
                % (m[1], n_coins, response, pricetarget, currency, total, currency,
                (time.time() - self.depth_cache[cachename]['time']),))
    asks = wrap(asks, [getopts({'over':'', 'market':'something', 'currency': 'currencyCode'}), 'nonNegativeFloat'])

    def bids(self, irc, msg, args, optlist, pricetarget):
        """[--under] [--market <market>] [--currency XXX] <pricetarget>
        
        Calculate the amount of bitcoin demanded at or over <pricetarget>.
        If '--under' option is given, find coins or at or under <pricetarget>.
        If market is supplied, uses that exchange. Default is %market%.
        If --currency XXX is provided, converts to that fiat currency. Default is USD.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency','USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        cachename = m[0]+currency
        response = "over"
        if dict(optlist).has_key('under'):
            f = lambda price,pricetarget: price <= pricetarget
            response = "under"
        else:
            f = lambda price,pricetarget: price >= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            bids = self.depth_cache[cachename]['depth']['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return
        for bid in bids:
            if f(bid['price'], pricetarget):
                n_coins += bid['amount']
                total += (bid['amount'] * bid['price'])

        irc.reply("%s | There are currently %.8g bitcoins demanded at "
                "or %s %s %s, worth %s %s in total."
                " | Data vintage: %.4f seconds"
                % (m[1], n_coins, response, pricetarget, currency, total, currency,
                (time.time() - self.depth_cache[cachename]['time']),))
    bids = wrap(bids, [getopts({'under':'', 'market':'something', 'currency': 'currencyCode'}), 'nonNegativeFloat'])

    def obip(self, irc, msg, args, optlist, width):
        """[--market <market>] [--currency XXX] <width>
        
        Calculate the "order book implied price", by finding the weighted
        average price of coins <width> BTC up and down from the spread.
        If market is supplied, uses that exchange. Default is %market%.
        If --currency XXX is provided, converts to that fiat currency. Default is USD.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency','USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        cachename = m[0]+currency
        try:
            asks = self.depth_cache[cachename]['depth']['asks']
            bids = self.depth_cache[cachename]['depth']['bids']
        except KeyError:
            irc.error("Failure to retrieve order book data. Try again later.")
            return

        b = self._buybtc(asks, width)
        s = self._sellbtc(bids, width)
        if b['all'] or s['all']:
            irc.error("The width provided extends past the edge of the order book. Please use a smaller width.")
            return
        obip = (b['total'] + s['total'])/2.0/width
        irc.reply("%s | The weighted average price of BTC, %s coins up and down from the spread, is %.5f %s."
                " | Data vintage: %.4f seconds"
                % (m[1], width, obip, currency, (time.time() - self.depth_cache[cachename]['time']),))
    obip = wrap(obip, [getopts({'market':'something', 'currency': 'currencyCode'}), 'positiveFloat'])

    def baratio(self, irc, msg, args, optlist):
        """[--market <market>] [--currency XXX]
        
        Calculate the ratio of total volume of bids in currency, to total btc volume of asks.
        If '--currency XXX' option is given, converts to currency denoted by given three-letter currency code. Default is USD.
        If market is supplied, uses that exchange. Default is %market%.
        """
        od = dict(optlist)
        market = od.pop('market',self.registryValue('defaultExchange'))
        currency = od.pop('currency', 'USD')
        m = self._getMarketInfo(market, 'depth')
        if m is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.depth_supported_markets.keys(),))
            return
        m[2](currency)
        try:
            asks = self.depth_cache[m[0]+currency]['depth']['asks']
            bids = self.depth_cache[m[0]+currency]['depth']['bids']
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
        irc.reply("%s | Total bids: %d %s. Total asks: %d BTC. Ratio: %.5f %s/BTC."
                " | Data vintage: %.4f seconds"
                % (m[1], totalbids, currency, totalasks, ratio, currency,
                (time.time() - self.depth_cache[m[0]+currency]['time']),))
    baratio = wrap(baratio, [getopts({'market':'something', 'currency': 'currencyCode'})])

    def _getMarketInfo(self, input, action='ticker'):
        sm = getattr(self, action + '_supported_markets')
        sml = sm.keys()+sm.values()
        dl = [dameraulevenshtein(input.lower(), i.lower()) for i in sml]
        if (min(dl) <= 2):
            mkt = (sml)[dl.index(min(dl))]
        else:
            return None
        if mkt.lower() in sm.keys():
            return [mkt.lower(), sm[mkt.lower()],
                    getattr(self, '_get' + mkt.capitalize() + action.capitalize()),]
        r = filter(lambda x: sm[x].lower() == mkt.lower(), sm)
        if len(r) == 1:
            return [r[0], sm[r[0]],
                    getattr(self, '_get' + r[0].capitalize() + action.capitalize()),]
        return None
        
    def premium(self, irc, msg, args, market1, market2):
        '''<market1> <market2>
        
        Calculate the premium of market1 over market2, using last trade price.
        Uses USD exchange rate. If USD is not traded on one of the target
        markets, queries currency conversion from google.
        '''
        r1 = self._getMarketInfo(market1)
        r2 = self._getMarketInfo(market2)
        if r1 is None or r2 is None:
            irc.error("This is not one of the supported markets. Please choose one of %s." % (self.ticker_supported_markets.keys(),))
            return
        try:
            last1 = float(r1[2]('USD')['last'])
            last2 = float(r2[2]('USD')['last'])
        except:
            irc.error("Failure to retrieve ticker. Try again later.")
            return
        prem = (last1-last2)/last2*100
        irc.reply("Premium of %s over %s is currently %s %%." % \
                (r1[1], r2[1], prem,))
    premium = wrap(premium, ['something','something'])
    
    def ticker(self, irc, msg, args, optlist):
        """[--bid|--ask|--last|--high|--low|--avg|--vol] [--currency XXX] [--market <market>|all]
        
        Return pretty-printed ticker. 
        If <market> is provided, uses that exchange. Default is %market%.
        If one of the result options is given, returns only that numeric result
        (useful for nesting in calculations).
        
        If '--currency XXX' option  is given, returns ticker for that three-letter currency code.
        It is up to you to make sure the code is a valid currency on your target market.
        Default currency is USD.
        """
        od = dict(optlist)
        currency = od.pop('currency', 'USD')
        market = od.pop('market',self.registryValue('defaultExchange'))
        r = self._getMarketInfo(market)
        if r is None and market.lower() != 'all':
            irc.error("This is not one of the supported markets. Please choose one of %s or 'all'" % (self.ticker_supported_markets.keys(),))
            return
        if len(od) > 1:
            irc.error("Please only choose at most one result option at a time.")
            return
        if market != 'all':
            try:
                ticker = r[2](currency)
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
                    (r[1], currency, ticker['bid'], ticker['ask'],
                    float(ticker['ask']) - float(ticker['bid']), ticker['last'],
                    ticker['vol'], ticker['low'], ticker['high'],
                    ticker['avg']))
            else:
                key = od.keys()[0]
                irc.reply(ticker[key])
        else:
            response = ""
            sumvol = 0
            sumprc = 0
            for mkt in ['btsp','btce','bfx','cbx','btcn', 'krk', 'bcent']:
                try:
                    r = self._getMarketInfo(mkt)
                    tck = r[2](currency)
                    response += "%s BTC%s last: %s, vol: %s | " % \
                            (r[1], currency, tck['last'], tck['vol'])
                except:
                    continue # we'll just skip this one then
                sumvol += float(tck['vol'])
                sumprc += float(tck['vol']) * float(tck['last'])
            response += "Volume-weighted last average: %s" % (sumprc/sumvol,)
            irc.reply(response)
    ticker = wrap(ticker, [getopts({'bid': '','ask': '','last': '','high': '',
            'low': '', 'avg': '', 'vol': '', 'currency': 'currencyCode', 'market': 'something'})])

#    def goxlag(self, irc, msg, args, optlist):
#        """[--raw]
#        
#        Retrieve mtgox order processing lag. If --raw option is specified
#        only output the raw number of seconds. Otherwise, dress it up."""
#        try:
#            json_data = urlopen("https://mtgox.com/api/2/money/order/lag").read()
#            lag = json.loads(json_data)
#            lag_secs = lag['data']['lag_secs']
#        except:
#            irc.error("Problem retrieving gox lag. Try again later.")
#            return
#
#        if dict(optlist).has_key('raw'):
#            irc.reply("%s" % (lag_secs,))
#            return
        
#        result = "MtGox lag is %s seconds." % (lag_secs,)
#        
#        au = lag_secs / 499.004784
#        meandistance = {0: "... nowhere, really",
#                        0.0001339: "to the other side of the Earth, along the surface",
#                        0.0024: "across the outer diameter of Saturn's rings",
#                        0.00257: "from Earth to Moon",
#                        0.002819: "from Jupiter to its third largest moon, Io",
#                        0.007155: "from Jupiter to its largest moon, Ganymede",
#                        0.00802: "from Saturn to its largest moon, Titan",
#                        0.012567: "from Jupiter to its second largest moon, Callisto",
#                        0.016: "one full loop along the orbit of the Moon around Earth",
#                        0.0257: 'ten times between Earth and Moon',
#                        0.0689: "approximately the distance covered by Voyager 1 in one week",
#                        0.0802: "ten times between Saturn and Titan",
#                        0.12567: "ten times between Jupiter and Callisto",
#                        0.2540: 'between Earth and Venus at their closest approach',
#                        0.257: 'one hundred times between Earth and Moon',
#                        0.2988: 'approximately the distance covered by Voyager 1 in one month',
#                        0.39: 'from the Sun to Mercury',
#                        0.72: 'from the Sun to Venus',
#                        1: 'from the Sun to Earth',
#                        1.52: 'from the Sun to Mars',
#                        2.77: 'from the Sun to Ceres (in the main asteroid belt)',
#                        5.2: 'from the Sun to Jupiter',
#                        9.54: 'from the Sun to Saturn',
#                        19.18: 'from the Sun to Uranus',
#                        30.06: 'from the Sun to Neptune',
#                        39.44: 'from the Sun to Pluto (Kuiper belt)',
#                        100: 'from the Sun to heliopause (out of the solar system!)'}
#        import operator
#        distances = meandistance.keys()
#        diffs = map(lambda x: abs(operator.__sub__(x, au)), distances)
#        bestdist = distances[diffs.index(min(diffs))]
#        objectname = meandistance[bestdist]
#        result += " During this time, light travels %s AU. You could have sent a bitcoin %s (%s AU)." % (au, objectname, bestdist)
#        irc.reply(result)
#    goxlag = wrap(goxlag, [getopts({'raw': ''})])

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

    def avgprc(self, irc, msg, args, currency, timeframe):
        """<currency> <timeframe>

        Returns volume-weighted average price data from BitcoinCharts.
        <currency> is a three-letter currency code, <timeframe> is
        the time window for the average, and can be '24h', '7d', or '30d'.
        """
        try:
            data = urlopen('http://api.bitcoincharts.com/v1/weighted_prices.json').read()
            j = json.loads(data)
            curs = j.keys()
            curs.remove('timestamp')
        except:
            irc.error("Failed to retrieve data. Try again later.")
            return
        try:
            result = j[currency.upper()][timeframe]
        except KeyError:
            irc.error("Data not available. Available currencies are %s, and "
                    "available timeframes are 24h, 7d, 30d." % (', '.join(curs),))
            return
        irc.reply(result)
    avgprc = wrap(avgprc, ['something','something'])

Class = Market


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
