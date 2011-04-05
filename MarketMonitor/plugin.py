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

import locale
import socket
import telnetlib
import threading
import time
import re
import json
import datetime

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
from supybot import schedule
from supybot import ircmsgs

class MarketMonitor(callbacks.Plugin):
    """Monitor a telnet push server for bitcoin trade data."""
    threaded = True
    callAfter = ['Services']
    def __init__(self, irc):
        self.__parent = super(MarketMonitor, self)
        self.__parent.__init__(irc)
        self.conn = telnetlib.Telnet()
        self.e = threading.Event()
        self.started = threading.Event()
        self.data = ""

    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        if irc.network == self.registryValue('network') and self.registryValue('autostart') and not self.started.isSet():
            self._start(irc)

    def _reconnect(self, repeat=True):
        while not self.e.isSet():
            try:
                self.conn.close()
                self.conn.open(self.registryValue('server'),
                                    self.registryValue('port'))
                return True
            except Exception, e:
                # this may get verbose, but let's leave this in for now.
                self.log.error('MarketMonitor: reconnect error: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                if not repeat:
                    return False
                time.sleep(5)

    def _monitor(self, irc):
        while not self.e.isSet():
            try:
                linedata = self.conn.read_until('\n', 1)
            except Exception, e:
                self.log.error('Error in MarketMonitor: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                self._reconnect()
                continue
            if linedata:
                output = self._parse(irc, linedata)
                if output:
                    for chan in self.registryValue('channels'):
                        irc.queueMsg(ircmsgs.privmsg(chan, output))
        self.started.clear()
        self.conn.close()

    def _parse(self, irc, msg):
        if not msg[-1] == '\n':
            self.data = self.data + msg
            return
        self.data = self.data + msg

        data = self.data

        #{"timestamp": 1302015318, "price": "0.7000", "volume": "0.27", "currency": "USD", "symbol": "btcexUSD"}

        if self.registryValue('format') == 'raw':
            self.data = ""
            return data

        try:
            d = json.loads(data)
            market = re.match(r'[a-z]+', d['symbol']).group(0)
            currency = re.search(r'[A-Z]+', d['symbol']).group(0)
            ts = datetime.datetime.utcfromtimestamp(d['timestamp']).strftime('%Y-%m-%d %H:%M:%S %Y UTC')
            out = "%s |%6s | %14s @ %s %s" % \
                    (ts, market, d['volume'], d['price'], currency)
            out = ircutils.bold(out)

            self.data = ""
            return out
        except:
            # we really want to keep going no matter what data we get
            self.log.error('MarketMonitor: Unrecognized data: %s' % data)
            self.data = ""
            return data

    def die(self):
        self.e.set()
        self.conn.close()
        self.__parent.die()

    def _start(self, irc):
        if not self.started.isSet():
            self.e.clear()
            self.started.set()
            success = self._reconnect(repeat=False)
            if success:
                t = threading.Thread(target=self._monitor, name='MarketMonitor',
                                     kwargs={'irc':irc})
                t.start()
                if hasattr(irc, 'reply'):
                    irc.reply("Monitoring start successful. Now monitoring market data.")
            else:
                if hasattr(irc, 'error'):
                     irc.error("Error connecting to server. See log for details.")
        else:
            irc.error("Monitoring already started.")

    def start(self, irc, msg, args):
        """takes no arguments

        Starts monitoring market data
        """
        irc.reply("Starting market monitoring.")
        self._start(irc)
    start = wrap(start, ['owner'])

    def stop(self, irc, msg, args):
        """takes no arguments

        Stops monitoring market data
        """
        irc.reply("Stopping market monitoring.")
        self.e.set()
    stop = wrap(stop, ['owner'])

Class = MarketMonitor

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
