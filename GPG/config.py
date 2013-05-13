###
# GPG - supybot plugin to authenticate users via GPG keys
# Copyright (C) 2011, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('GPG', True)


GPG = conf.registerPlugin('GPG')

conf.registerGlobalValue(GPG, 'authRequestTimeout',
    registry.NonNegativeInteger(300, """Time (seconds) for authentication
    requests to time out."""))
conf.registerGlobalValue(GPG, 'keyservers',
    registry.String("subset.pool.sks-keyservers.net,pgp.mit.edu", """Default keyservers to
    use for key retrieval. Comma-separated list."""))
conf.registerGlobalValue(GPG, 'channels',
    registry.String("#bitcoin-otc", """Channels to monitor for user parts
    for auth removal. Semicolon-separated list."""))
conf.registerGlobalValue(GPG, 'network',
    registry.String("freenode", """Network to monitor for user parts/quits
    and bot quits for auth removal."""))
conf.registerGlobalValue(GPG, 'pastebinWhitelist',
    registry.SpaceSeparatedListOfStrings(['http://pastebin.com','http://paste.debian.net'], 
    """If set, bot will only fetch clearsigned data
    for the verify command from urls in the whitelist, i.e. starting with
    http://domain/optionalpath/."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
