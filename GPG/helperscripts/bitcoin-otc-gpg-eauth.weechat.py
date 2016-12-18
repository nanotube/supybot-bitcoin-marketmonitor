# -*- coding: utf-8 -*-
# otc-auth - WeeChat script for authenticating to #bitcoin-otc gribble bot
#
#
# Copyright (c) 2013 Your Mother's Favorite Programmer
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Imports
try:
    import weechat as w
except ImportError:
    print 'This script must be run under WeeChat.'
    print 'Get WeeChat now at: http://www.weechat.org'
    quit()
try:
    import requests
except ImportError:
    print 'This script requires the requests module.'
    print 'Get it using: pip-2.7 install requests'
    quit()

import re
import tempfile
import time

# Constants
SCRIPT_NAME = 'otc-auth'
SCRIPT_DESC = 'Authenticate to Gribble Bot in freenode\'s #bitcoin-otc'
SCRIPT_HELP = """%s

Authenticate to gribble in freenode's #bitcoin-otc.
Currently only supports gpg authentication.

Future versions will support bitcoin auth using bitcoin-python.

Requires the shell.py script available at:
    http://www.weechat.org/scripts

""" % SCRIPT_DESC

SCRIPT_AUTHOR = 'Your Mother\'s Favorite Programmer'
SCRIPT_LICENSE = 'GPL3'
SCRIPT_VERSION = '1.1.0'

OTC_URL = 'http://bitcoin-otc.com/otps/{}'
OTC_RE = re.compile(r'http://bitcoin-otc.com/otps/[A-Z0-9]+')

# Default config values
settings = { 'gpg_id'  : '-'     # gpg id for auth'ing w/ gribble
           , 'pw_to'   : '15'    # no. of secs to allow gpg pw entry
           }

def get_challenge(gpg_id):
    # Make a request to the site
    r = requests.get(OTC_URL.format(gpg_id))
    
    # Return the text of the GET
    return r.text

def decrypt_challenge(challenge):
    # Use a temporary file for decryption
    with open('/tmp/e', 'w') as tf:
        # Write out the challenge to the file
        tf.write(challenge)

    # Use GPG to decrypt this (df == decrypted file)
    with tempfile.NamedTemporaryFile() as df:
        cmd = 'gpg --yes --batch -o {} -d {}'.format(df.name, '/tmp/e')
        w.command( ''
                 , '/shell {}'.format(cmd)
                 )
        time.sleep(int(settings['pw_to']))
        result = df.read()
        os.remove('/tmp/e')

    w.command( ''
             , '/query gribble ;;gpg everify {}'.format(result)
             )

def otc_auth_cmd(data, buffer, args):
    '''
    Run when /otc-auth is entered into weechat.
    '''
    # Check for gpg_id config option
    if settings['gpg_id'] != '-':
        decrypt_challenge(get_challenge(settings['gpg_id']))
    else:
        # Obtain the gpg ID 
        if args:
            try:
                nick, pw_to = args.split()

                # Save the pw_to in the settings dict
                global settings
                settings['pw_to'] = pw_to
            except ValueError:
                nick = args
        else:
            server = w.buffer_get_string(w.current_buffer(), 'localvar_server')
            nick = w.info_get('irc_nick', server)

        # Query gribble for eauth
        # Will open up a new window
        w.command( ''
                 , '/query gribble ;;gpg eauth {}'.format(nick)
                 ) 

    return w.WEECHAT_RC_OK
    
def priv_msg_cb(data, bufferp, uber_empty, tagsn, isdisplayed,
                ishighlight, prefix, message):
    '''
    Executed when gribble replies back to the ;;gpg eauth command.
    '''
    is_pm = w.buffer_get_string(bufferp, 'localvar_type') == 'private'
    if is_pm:
        # Parse out the gpg_id
        gpg_id = OTC_RE.findall(message)[0].split('/')[-1]

        # Get the challenge and decrypt it
        decrypt_challenge(get_challenge(gpg_id))

        # Clear the buffer to fix any issues from gpg
        w.buffer_clear(w.current_buffer())

    return w.WEECHAT_RC_OK

#-------------------------#
#                         #
#         MAIN            #
#                         #
#-------------------------#
if __name__ == '__main__':
    # Mandatory register function
    if w.register( SCRIPT_NAME
                 , SCRIPT_AUTHOR
                 , SCRIPT_VERSION
                 , SCRIPT_LICENSE
                 , SCRIPT_DESC
                 , ''
                 , ''
                 ):

        # Check the config value
        global settings
        for opt, def_val in settings.items():
            if not w.config_is_set_plugin(opt):
                w.config_set_plugin(opt, def_val)
            else:
                configp = w.config_get('plugins.var.python.otc-auth.%s' % opt)
                config_val = w.config_string(configp)
                settings[opt] = config_val

        # Create the command
        w.hook_command( 'otc-auth'
                      , 'Authenticates with gribble bot in #bitcoin-otc'
                      , '[username] [password timeout]'
                      , 'Currently only supports gpg authentication.\n'
                        'Requires a username if the name you auth.\n'
                        'with is different from your nick on freenode.\n\n'
                        'Password timeout is the number of seconds you\n'
                        'have to enter in your private key\'s password.\n'
                        'Requires the installation of shell.py:\n'
                        '   /script install shell.py\n\n'
                        'After execution, use Ctrl+L to reset your screen.\n'
                      , ''
                      , 'otc_auth_cmd'
                      , ''
                      )

        # Get notifications of gribble query
        w.hook_print('', 'irc_privmsg', '', 1, 'priv_msg_cb', '')
