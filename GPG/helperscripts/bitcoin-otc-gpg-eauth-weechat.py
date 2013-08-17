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
    import requests
except ImportError:
    print 'This script requires the requests module.'
    print 'Get it using: pip-2.7 install requests'
    quit()

import re
import tempfile
import time

try:
    import weechat as w
except ImportError:
    print 'This script must be run under WeeChat.'
    print 'Get WeeChat now at: http://www.weechat.org'
    quit()

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
settings = { 'gpg'     : 'yes'   # using gpg auth vs. bitcoin
           , 'pw_to'   : '25'    # no. of secs to allow gpg pw entry
           }


#-----------------------------------------------------------#
#                                                           #
#                      GPG Functions                        #
#                                                           #
#-----------------------------------------------------------#
def get_challenge(gpg_id):
    # Make a request to the site
    r = requests.get(OTC_URL.format(gpg_id))
    
    # Return the text of the GET
    return r.text

def decrypt_challenge(challenge):
    # Use a temporary file for decryption
    with tempfile.NamedTemporaryFile(mode='w+') as tf:
        # Write out the challenge to the file
        tf.write(challenge)

        # Use GPG to decrypt this (df == decrypted file)
        with tempfile.NamedTemporaryFile(mode='w+') as df:
            tf.seek(0)
            cmd = 'gpg --yes --batch -o {} -d {}'.format(df.name, tf.name)
            w.command( ''
                     , '/shell {}'.format(cmd)
                     )
            time.sleep(int(settings['pw_to']))
            df.seek(0)
            result = df.read()

    w.command( ''
             , '/query gribble ;;gpg everify {}'.format(result)
             )

#-----------------------------------------------------------#
#                                                           #
#             WeeChat Functions and Callbacks               #
#                                                           #
#-----------------------------------------------------------#
def otc_auth_cmd(data, buffer, args):
    '''
    Run when /otc-auth is entered into weechat.
    '''
    global settings

    # Obtain the gpg ID 
    if args:
        try:
            nick, pw_to = args.split()

            # Save the pw_to in the settings dict
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
        btc_urls = OTC_RE.findall(message)
        if btc_urls:
            # Get the gpg id for fetching the challenge
            gpg_id = btc_urls[0].split('/')[-1]

            # Get the challenge and decrypt it
            decrypt_challenge(get_challenge(gpg_id))

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
        for opt, def_val in settings.items():
            if not w.config_is_set_plugin(opt):
                w.config_set_plugin(opt, def_val)
            else:
                # Move the saved config values into the dict
                configp = w.config_get('plugins.var.python.otc-auth.%s' % opt)
                config_val = w.config_string(configp)
                settings[opt] = config_val

        # Create the command
        w.hook_command( 'otc-auth'
                      , 'Authenticate with gribble bot in #bitcoin-otc.'
                      , '[username] [password timeout]'
                      , 'Currently only supports gpg authentication.\n'
                        'Requires a username if the name you auth\n'
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
        w.hook_print('', 'irc_privmsg', 'http://bitcoin-otc.com', 1, 'priv_msg_cb', '')
