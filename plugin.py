###
# Copyright (c) 2010, mizerydearia
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

import socket
import telnetlib
import threading
import time

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world

class MarketMonitor(callbacks.Plugin):
    """Add the help for "@plugin help MarketMonitor" here
    This should describe *how* to use this plugin."""
    #threaded = True

    def __init__(self, irc):
        self.__parent = super(MarketMonitor, self)
        self.__parent.__init__(irc)
        self.telnetBCM = telnetlib.Telnet()
        self.e = threading.Event()
        
    def die(self):
        self.telnetBCM.close()
        self.__parent.die()

    def restart(self, irc, msg, args):
        self.stop(self, irc, msg, args)
        self.start(self, irc, msg, args)
    restart = wrap(restart)

    def _monitor(self, irc):
        while not self.e.isSet():
            try:
                irc.reply('event status: %s' % self.e.isSet(), prefixNick=False)
                irc.reply('trying for 5 seconds', prefixNick=False)
                linedata = self.telnetBCM.read_until('\n', 5)
            except EOFError, e:
                irc.error(str(e))
                break
            except Exception, e:
                irc.reply(str(e))
                break

            if linedata:
                irc.reply(linedata.lower(), prefixNick=False)

        irc.reply('After while loop', prefixNick=False)
        self.telnetBCM.close()

    def start(self, irc, msg, args):
        """takes no arguments

        Starts monitoring market data
        """
        irc.reply('starting', prefixNick=False)
        self.e.clear()
        
        try:
            self.telnetBCM.open('bitcoinmarket.com', 27007)
        except socket.error, e:
            irc.error(str(e))
            return
        t = threading.Thread(target=self._monitor, kwargs={'irc':irc})
        t.start()
    start = wrap(start)

    def stop(self, irc, msg, args):
        """takes no arguments

        Stops monitoring market data
        """
        print "in stop function!"
        irc.reply('stopping', prefixNick=False)
        self.e.set()
        #self.telnetBCM.close()
    stop = wrap(stop)

Class = MarketMonitor

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: