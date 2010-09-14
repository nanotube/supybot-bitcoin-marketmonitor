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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import ircmsgs

import threading
import time
import json

class MtgoxMonitor(callbacks.Plugin):
    """This plugin monitors the Mtgox marketplace for activity.

    Use 'start' command to start monitoring, 'stop' command to stop.
    """

    def __init__(self, irc):
        self.__parent = super(MtgoxMonitor, self)
        self.__parent.__init__(irc)
        self.last_checked = time.time()
        #self.depth_dict = {}
        self.e = threading.Event()
        self.started = threading.Event()

    def _monitorMtgoxTrades(self, irc):
        while not self.e.isSet():
            try:
                new_trades = utils.web.getUrl('http://mtgox.com/code/data/getTrades.php')
            except:
                continue # let's just try again.
            checked = time.time()
            new_trades = json.loads(new_trades, parse_float=str, parse_int=str)
            #new_depth = utils.web.getUrl('http://mtgox.com/code/getDepth.php')
            #new_depth = json.loads(new_depth, parse_float=str, parse_int=str)
            for trade in new_trades:
                if float(trade['date']) > self.last_checked:
                    out = "MTG|%10s|%27s @ %-10s %24s" % \
                          ('TRADE',
                           trade['amount'],
                           '$' + trade['price'],
                           time.strftime("%b %d %Y %H:%M:%S GMT", time.gmtime()))
                    for chan in self.registryValue('channels'):
                        irc.queueMsg(ircmsgs.privmsg(chan, out))
            self.last_checked = checked
            time.sleep(self.registryValue('pollinterval'))
        self.started.clear()

    def start(self, irc, msg, args):
        """Start monitoring MtGox data."""
        if not self.started.isSet():
            self.e.clear()
            self.started.set()
            t = threading.Thread(target=self._monitorMtgoxTrades,
                                 kwargs={'irc':irc})
            t.start()
            irc.reply("Monitoring start successful. Now reporting Mtgox trades.")
        else:
            irc.error("Monitoring already started.")
    start = wrap(thread(start))

    def stop(self, irc, msg, args):
        irc.reply("Stopping Mtgox monitoring.")
        self.e.set()
    stop = wrap(stop)

    def die(self):
        self.e.set()
        self.__parent.die()



Class = MtgoxMonitor


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
