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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
from supybot import schedule
from supybot import ircmsgs

class MarketMonitor(callbacks.Plugin):
    """Add the help for "@plugin help MarketMonitor" here
    This should describe *how* to use this plugin."""
    #threaded = True

    def __init__(self, irc):
        self.__parent = super(MarketMonitor, self)
        self.__parent.__init__(irc)
        self.telnetBCM = telnetlib.Telnet()
        self.e = threading.Event()
        self.started = threading.Event()
        self.data = ""
#        channels = self.registryValue('channels')
#        if channels:
#            def f():
#                self._autostart(irc)
#            schedule.addEvent(

    def _reconnect(self, repeat=True):
        while not self.e.isSet():
            try:
                self.telnetBCM.close()
                self.telnetBCM.open(self.registryValue('server'),
                                    self.registryValue('port'))
                return True
            except Exception, e:
                # this may get verbose, but let's leave this in for now.
                self.log.error('MarketMonitor: reconnect error: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                if not repeat:
                    return False
                time.sleep(5)

    def _monitorBCM(self, irc):
        while not self.e.isSet():
            try:
                linedata = self.telnetBCM.read_until('\n', 1)
            except Exception, e:
                self.log.error('Error in MarketMonitor: %s: %s' % \
                            (e.__class__.__name__, str(e)))
                self._reconnect()
                continue
            if linedata:
                output = self._parseBCM(irc, linedata)
                if output:
                    for chan in self.registryValue('channels'):
                        irc.queueMsg(ircmsgs.privmsg(chan, output))
        self.started.clear()
        self.telnetBCM.close()

    # http://code.activestate.com/recipes/473872-number-format-function-a-la-php/#c3
    def _number_format(self, num, places=0):
        locale.setlocale(locale.LC_NUMERIC, '')
        return locale.format("%.*f", (places, num), True)

    def _parseBCM(self, irc, msg):
        if not msg[-1] == '\n':
            self.data = self.data + msg
            return
        self.data = self.data + msg

        data = self.data

        # New-Bid: ID:2478 Currency:PayPalUSD Price:0.0100 Quantity:1000
        # Cancelled-Bid: ID:2468 Currency:PayPalUSD Price:0.0010 Quantity:100
        # New-Trade: ID:692 Currency:PecunixGAU Price:0.001560 Quantity:1500
        # Confirmed-Trade: ID:695 Currency:PecunixGAU Price:0.001700 Quantity:4000
        # New-Bid, New-Ask, Cancelled-Bid, Cancelled-Ask, New-Trade, Cancelled-Trade, Confirmed-Trade

        if self.registryValue('format') == 'raw':
            self.data = ""
            return data

        if data.find("WELCOME TO BITCOIN MARKET STREAMING QUOTES") > -1:
            self.data = ""
            return

        trans_type_dict = {'New-Bid':'NEW BID',
                           'New-Ask':'NEW ASK',
                           'Cancelled-Bid':'UNBID',
                           'Cancelled-Ask':'UNASK',
                           'New-Trade':'NEW TRD',
                           'Cancelled-Trade':'UNTRD',
                           'Confirmed-Trade':'CONF TRD'}

        currency_name_dict = {'LibertyReserveUSD':'LRUSD',
                              'MoneyBookersUSD':'MBUSD',
                              'PayPalUSD':'PPUSD',
                              'PecunixGAU':'PXGAU'}

        currency_sym_dict = {'LibertyReserveUSD':'$',
                              'MoneyBookersUSD':'$',
                              'PayPalUSD':'$',
                              'PecunixGAU':'GAU'}

        try:
            m_type = re.search(r'(' + '|'.join(trans_type_dict.keys()) + ')', data)
            trans_type = m_type.group(1)

            m_curr = re.search(r'(' + '|'.join(currency_name_dict.keys()) + ')', data)
            trans_curr = m_curr.group(1)

            m_quant = re.search(r'Quantity:([\d\.]+)', data)
            trans_quant = m_quant.group(1)

            m_price = re.search(r'Price:([\d\.]+)', data)
            trans_price = m_price.group(1)

            m_id = re.search(r'ID:(\d+)', data)
            trans_id = m_id.group(1)

            out = "BCM|%10s|%5s %21s @ %-10s %s" % \
                  (trans_type_dict[trans_type],
                   currency_name_dict[trans_curr],
                   self._number_format(float(trans_quant)),
                   currency_sym_dict[trans_curr] + trans_price,
                   time.strftime("%b %d %Y %H:%M:%S GMT", time.gmtime()))

            self.data = ""
            return out
        except:
            # we really want to keep going no matter what data we get
            self.log.error('MarketMonitor: Unrecognized data: %s' % data)
            self.data = ""
            return data

    def die(self):
        self.e.set()
        self.telnetBCM.close()
        self.__parent.die()

    def restart(self, irc, msg, args):
        self.stop(self, irc, msg, args)
        self.start(self, irc, msg, args)
    restart = wrap(restart)

    def _autostart(self, irc):
        self.e.clear()
        success = self._reconnect(repeat=False)
        if success:
            t = threading.Thread(target=self._monitorBCM, kwargs={'irc':irc})
            t.start()

    def start(self, irc, msg, args):
        """takes no arguments

        Starts monitoring market data
        """
        if not self.started.isSet():
            self.e.clear()
            self.started.set()
            success = self._reconnect(repeat=False)
            if success:
                t = threading.Thread(target=self._monitorBCM, kwargs={'irc':irc})
                t.start()
                irc.reply("Connection successful. Now monitoring for activity.")
            else:
                irc.error("Error connecting to server. See log for details.")
        else:
            irc.error("Monitoring already started.")
    start = wrap(start)

    def stop(self, irc, msg, args):
        """takes no arguments

        Stops monitoring market data
        """
        irc.reply("Stopping BCM monitoring.")
        self.e.set()
    stop = wrap(stop)

Class = MarketMonitor

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
