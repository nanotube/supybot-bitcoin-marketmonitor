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
import threading
import time
import re
import json
import datetime
from urllib2 import urlopen

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
from supybot import ircmsgs

class MarketMonitorTicker(callbacks.Plugin):
    """Monitor a telnet push server for bitcoin trade data."""
    threaded = True
    callAfter = ['Services']
    def __init__(self, irc):
        self.__parent = super(MarketMonitorTicker, self)
        self.__parent.__init__(irc)
        self.e = threading.Event()
        self.started = threading.Event()
        self.cachedticker = None
        self.freshticker = None

    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        if not self.started.isSet() and irc.network == self.registryValue('network') and self.registryValue('autostart'):
            self._start(irc)

    def _getTicker(self):
        json_data = urlopen(self.registryValue('tickerUrl')).read()
        ticker = json.loads(json_data)
        return ticker['return']

    def _monitor(self, irc):
        while not self.e.isSet():
            self.freshticker = None
            try:
                self.freshticker = self._getTicker()
            except Exception, e:
                self.log.error('Error in MarketMonitorTicker: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                continue
            try:
                if irc.getCallback('Services').identified and self.freshticker is not None:
                    output = self._processdata()
                    if output:
                        for chan in self.registryValue('channels'):
                            irc.queueMsg(ircmsgs.privmsg(chan, output))
            except Exception, e:
                self.log.error('Error in MarketMonitorTicker: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                continue # keep going no matter what
            time.sleep(self.registryValue('pollInterval'))
        self.started.clear()

    def _processdata(self):
        # if we have difference in bid/ask/last, or if cachedticker is missing
        # make output.
        makeoutput = False
        
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime("%b%d %H:%M:%S")
        
        datalist = [timestamp,
                    self.freshticker['buy']['value'],
                    self.freshticker['sell']['value'],
                    self.freshticker['last']['value'],
                    self.freshticker['vol']['value']
		    ]
        colorlist = ['light gray'] * 5
        
        if self.cachedticker is None:
            self.cachedticker = self.freshticker
            makeoutput = True
            
        if self.freshticker['buy'] != self.cachedticker['buy'] or \
            self.freshticker['sell'] != self.cachedticker['sell'] or \
            self.freshticker['last'] != self.cachedticker['last']:
            
            makeoutput = True
            
            colorlist = ['light gray',]
            for item in ['buy','sell','last','vol']:
                if self.freshticker[item] > self.cachedticker[item]:
                    colorlist.append('green')
                elif self.freshticker[item] < self.cachedticker[item]:
                    colorlist.append('red')
                else:
                    colorlist.append('light gray')

        coloredlist = map(ircutils.mircColor, datalist, colorlist)
        
        self.cachedticker = self.freshticker
        
        if makeoutput:
            output = "{time} | Bid: {bid:<12} | Ask: {ask:<12} | Last: {last:<12} | Volume: {vol}".format(time=coloredlist[0],
                    bid=coloredlist[1],
                    ask=coloredlist[2],
                    last=coloredlist[3],
                    vol=coloredlist[4])
            return output
        else:
            return False

    def die(self):
        self.e.set()
        self.__parent.die()

    def _start(self, irc):
        if not self.started.isSet():
            self.e.clear()
            self.started.set()
            t = threading.Thread(target=self._monitor, name='MarketMonitorTicker',
                                     kwargs={'irc':irc})
            t.start()
            if hasattr(irc, 'reply'):
                irc.reply("Monitoring start successful. Now monitoring market data.")
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

Class = MarketMonitorTicker


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
