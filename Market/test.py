###
# Copyright (c) 2011, remote
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

class MarketTestCase(PluginTestCase):
    plugins = ('Market',)

    def testAsks(self):
        self.assertError('asks blabla')
        self.assertRegexp('asks 0', 'There are currently 0 bitcoins offered at or under 0')
        self.assertRegexp('asks --over 5.5', 'There are currently .* bitcoins offered at or over 5')

    def testBids(self):
        self.assertError('bids blabla')
        self.assertRegexp('bids 10000000', 'There are currently 0 bitcoins demanded at or over 1')
        self.assertRegexp('bids --under 5.5', 'There are currently .* bitcoins demanded at or under 5')

    def testTicker(self):
        self.assertRegexp('ticker', 'Best bid')
        self.assertRegexp('ticker --bid', '[\d\.]+')
        self.assertRegexp('ticker --ask', '[\d\.]+')
        self.assertRegexp('ticker --last', '[\d\.]+')
        self.assertRegexp('ticker --high', '[\d\.]+')
        self.assertRegexp('ticker --low', '[\d\.]+')
        self.assertError('ticker --last --bid')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
