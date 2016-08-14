###
# Copyright (c) 2010, mizerydearia
# Copyright (c) 2010, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
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

import decimal
import locale
import threading
import time
import re
import json
import datetime
import Queue
import sys
import urllib2

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
from supybot import schedule
from supybot import ircmsgs
from supybot import conf

class MarketMonitor(callbacks.Plugin):
    """Monitor a telnet push server for bitcoin trade data."""
    threaded = True
    callAfter = ['Services']
    def __init__(self, irc):
        self.__parent = super(MarketMonitor, self)
        self.__parent.__init__(irc)
        self.e = threading.Event()
        self.started = threading.Event()
        self.data = ""

        self.marketdata = {}
        # Example: {("mtgox", "USD"): [(volume, price, timestamp),(volume, price, timestamp)], ("th", "USD"): [(volume, price, timestamp)]}
        
        self.raw = []
        self.nextsend = time.time() # Timestamp for when we can send next. Handling this manually allows better collapsing.
        
        self.q = Queue.Queue()

    def _start_data_pullers(self):
        self.data_threads = {}
        self.markets = self.registryValue('supportedMarkets') # ['Bitstamp', 'GDAX', 'Bitfinex']
        current_module = sys.modules[__name__]
        for market in self.markets:
            self.data_threads[market] = getattr(current_module, 'Read'+market+'Trades')(self.q, market)
            self.data_threads[market].start()

    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        if not self.started.isSet() and irc.network == self.registryValue('network') and self.registryValue('autostart'):
            self._start(irc)

    def _monitor(self, irc):
        while not self.e.isSet():
            try:
                chunk = self.q.get(True, 10)
                k,v = chunk.items()[0]
                self.marketdata[k] = v
            except Queue.Empty:
                continue
            except Exception, e:
                self.log.error('Error in MarketMonitor queue: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                continue # keep going no matter what
            try:
                if time.time() >= self.nextsend:
                    outputs = self._format()
                    if outputs:
                        for output in outputs:
                            for chan in self.registryValue('channels'):
                                irc.queueMsg(ircmsgs.privmsg(chan, output))
                        self.nextsend = time.time()+(conf.supybot.protocols.irc.throttleTime() * len(outputs))
                    self.marketdata = {}
                    self.raw = []
            except Exception, e:
                self.log.error('Error in MarketMonitor sending: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                continue # keep going no matter what
            time.sleep(0.01)
        self.started.clear()

    def _format(self):
        if self.registryValue('format') == 'raw':
            return [x.rstrip() for x in self.raw]

        # Making a pretty output
        outputs = []
        try:
            for (market, currency), txs in self.marketdata.iteritems():
                if len(txs) >= self.registryValue('collapseThreshold'):
                    # Collapse transactions to a single transaction with degeneracy
                    (sumvol, sumpr, sumst) = reduce((lambda (sumvol, sumpr, sumst), (vol, pr, st): (sumvol+vol, sumpr+(pr*vol), sumst+(st*vol))), txs, (0,0,0))
                    degeneracy = "x" + str(len(txs))
                    txs = [(sumvol, sumpr/sumvol, sumst/sumvol)]
                else:
                    degeneracy = ""
                for (vol, pr, st) in txs:
                    prfmt = self._moneyfmt(pr, places=8)
                    match = re.search(r"\.\d{2}[0-9]*?(0+)$", prfmt)
                    if match is not None:
                        # pad off the trailing 0s with spaces to retain justification
                        numzeros = len(match.group(1))
                        prfmt = prfmt[:-numzeros] + (" " * numzeros)
                    # don't forget to count irc bold marker character on both ends of bolded items
                    if len(self.registryValue('marketsWhitelist')) == 0 or market in self.registryValue('marketsWhitelist'):
                        out = "{time} {mkt:10} {num:>4} {vol:>10} @ {pr:>16} {cur}".format(time=datetime.datetime.utcfromtimestamp(st).strftime("%b%d %H:%M:%S"),
                                mkt=ircutils.bold(market), num=degeneracy, vol=self._moneyfmt(vol, places=4), pr=ircutils.bold(prfmt), cur=currency)
                        outputs.append((st,out))

            outputs.sort()
        except Exception, e:
            # we really want to keep going no matter what data we get
            self.log.error('Error in MarketMonitor formatting: %s: %s' % \
                            (e.__class__.__name__, str(e)))
            self.log.error('MarketMonitor: Unrecognized data: %s' % self.marketdata)
            return False
        return [out for (_,out) in outputs]

    def die(self):
        self.e.set()
        self.__parent.die()

    def _start(self, irc):
        if not self.started.isSet():
            self.e.clear()
            
            #success = self._reconnect(repeat=False)
            #if success:
            t = threading.Thread(target=self._monitor, name='MarketMonitor',
                                 kwargs={'irc':irc})
            t.start()
            if hasattr(irc, 'reply'):
                irc.reply("Monitoring start successful. Now monitoring market data.")
            self._start_data_pullers()
            self.started.set()
            
            #else:
                #if hasattr(irc, 'error'):
                     #irc.error("Error connecting to server. See log for details.")
        else:
            irc.error("Monitoring already started.")

    def start(self, irc, msg, args):
        """takes no arguments

        Starts monitoring market data
        """
        irc.reply("Starting market monitoring.")
        self._start(irc)
    start = wrap(start, [('checkCapability', 'monitor')])

    def stop(self, irc, msg, args):
        """takes no arguments

        Stops monitoring market data
        """
        irc.reply("Stopping market monitoring.")
        self.e.set()
        for k,v in self.data_threads.iteritems():
            v.stop()
        
    stop = wrap(stop, [('checkCapability', 'monitor')])

    def _moneyfmt(self, value, places=2, curr='', sep=',', dp='.', pos='', neg='-',
        trailneg=''):
        """Convert Decimal to a money formatted string.

        places:  required number of places after the decimal point
        curr:    optional currency symbol before the sign (may be blank)
        sep:     optional grouping separator (comma, period, space, or blank)
        dp:      decimal point indicator (comma or period)
                 only specify as blank when places is zero
        pos:     optional sign for positive numbers: '+', space or blank
        neg:     optional sign for negative numbers: '-', '(', space or blank
        trailneg:optional trailing minus indicator:  '-', ')', space or blank

        >>> d = Decimal('-1234567.8901')
        >>> moneyfmt(d, curr='$')
        '-$1,234,567.89'
        >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
        '1.234.568-'
        >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
        '($1,234,567.89)'
        >>> moneyfmt(Decimal(123456789), sep=' ')
        '123 456 789.00'
        >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
        '<0.02>'

        """
        q = decimal.Decimal(10) ** -places      # 2 places --> '0.01'
        sign, digits, exp = value.quantize(q).as_tuple()
        result = []
        digits = map(str, digits)
        build, next = result.append, digits.pop
        if sign:
            build(trailneg)
        for i in range(places):
            build(next() if digits else '0')
        build(dp)
        if not digits:
            build('0')
        i = 0
        while digits:
            build(next())
            i += 1
            if i == 3 and digits:
                i = 0
                build(sep)
        build(curr)
        build(neg if sign else pos)
        return ''.join(reversed(result))

Class = MarketMonitor

class BaseTradeReader(threading.Thread):
    def __init__(self, q, market):
        threading.Thread.__init__(self, name=market+'Monitor')
        self.q = q
        self.e = threading.Event()
        self.market = market
        self.trades_api_url = ''
    
    def run(self):
        pass
        
    def stop(self):
        self.e.set()
    
        
class ReadBitfinexTrades(BaseTradeReader):
    def __init__(self, q, market):
        BaseTradeReader.__init__(self, q, market)
        self.trades_api_url = 'https://api.bitfinex.com/v1/trades/BTCUSD'
        self.timestamp = None
        self.prev_timestamp_tids = []
        # ?timestamp=epoch
        #~ [{
          #~ "timestamp":1444266681,
          #~ "tid":11988919,
          #~ "price":"244.8",
          #~ "amount":"0.03297384",
          #~ "exchange":"bitfinex",
          #~ "type":"sell"
        #~ }]
        # most recent trade first
    
    def run(self):
        while not self.e.is_set():
            if self.timestamp is None: # so we don't glom together a day's worth of trades at startup.
                self.timestamp = time.time() - 600
            data = json.loads(urllib2.urlopen(self.trades_api_url + \
                    '?timestamp=' + str(self.timestamp)).read())
            if 'message' in data:
                continue # some error... oh well.
            self.timestamp = data[0]['timestamp']
            
            timestamp_tids = filter(lambda x: x['timestamp'] == self.timestamp, data)
            data = filter(lambda x: x['tid'] not in self.prev_timestamp_tids, data)
            self.prev_timestamp_tids = [t['tid'] for t in timestamp_tids]
            
            trades = [(decimal.Decimal(str(t['amount'])),
                    decimal.Decimal(str(t['price'])),
                    decimal.Decimal(str(t['timestamp']))) for t in reversed(data)]
            
            #for t in reversed(trades):
                #self.q.put(json.dumps(t))
            self.q.put({(self.market, 'USD'): trades})
            
            time.sleep(10)

class ReadBitstampTrades(BaseTradeReader):
    def __init__(self, q, market):
        BaseTradeReader.__init__(self, q, market)
        self.trades_api_url = 'https://www.bitstamp.net/api/v2/transactions/btcusd/?time=minute'
        self.prev_tids = []
        #~ date	Unix timestamp date and time.
        #~ tid	Transaction ID.
        #~ price	BTC price.
        #~ amount	BTC amount.
        #~ type	0 (buy) or 1 (sell).
        # most recent first
    
    def run(self):
        while not self.e.is_set():
            try:
                data = json.loads(urllib2.urlopen(self.trades_api_url).read())
            except:
                continue
            
            tids = [t['tid'] for t in data]
            data = filter(lambda x: x['tid'] not in self.prev_tids, data)
            self.prev_tids = tids
            
            trades = [(decimal.Decimal(str(t['amount'])),
                    decimal.Decimal(str(t['price'])),
                    decimal.Decimal(str(t['date']))) for t in reversed(data)]

            self.q.put({(self.market, 'USD'): trades})
            
            time.sleep(10)

class ReadGDAXTrades(threading.Thread):
    def __init__(self, q, market):
        threading.Thread.__init__(self)
        self.q = q
        self.market = market
        self.trades_api_url = ''
    def run(self):
        pass # will read data from trades api here


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
