__module_name__ = 'OTC Auto Eauth'
__module_version__ = '0.3.0'
__module_description__ = 'Automatic eauth for gribble in Freenode #bitcoin-otc. Version 0.2.0 by nanotube <nanotube@users.sourceforge.net>, based on version 0.1.0 by Delia Eris <asphodelia.erin@gmail.com>.'

###############
# ----USER GUIDE----
#
# This script WILL NOT work 'out of the box'.
# You MUST edit the lines marked below as instructed.
#
# You must also have the python-gnupg module. At a minimum,
# get gnupg.py from http://code.google.com/p/python-gnupg/
# and stick it into your .xchat2 directory next to this plugin.
# Or just install it with its setup.py in the usual python fashion.
#
# To initiate authentication, run command /eauth
# Enter your GPG passphrase into the prompt box (blank if none)
# Enjoy being authenticated!
# 
# License: CC0. Attribution is cool, plagiarism isn't.
##############

import xchat
import urllib
import sys
import re

print '\0034',__module_name__, __module_version__,'has been loaded.\003'

# Set this to the correct path to your GPG directory.
_gpghome = '/home/YOUR_USERNAME/.gnupg'
# Set this to your OTC nick.
_otcnick = 'OTC_NICK'
# Set to path where you put gnupg.py, if not in default python search path
_gnupgdir = '/home/YOUR_USERNAME/.xchat2/'

sys.path.append(_gnupgdir)
import gnupg

gpg = gnupg.GPG(gnupghome=_gpghome)

def askpw_cb(word, word_eol, userdata):
    pw = word_eol[0]
    xchat.pw = pw[6:]
    if xchat.pw == "":
        xchat.pw = None
    response_data = str(gpg.decrypt(xchat.challenge_data, passphrase = xchat.pw)).rstrip()
    m = re.search("freenode:#bitcoin-otc:[a-f0-9]{56}", response_data)
    if m is not None:
        xchat.command('msg gribble ;;everify '+ m.group(0))
    else:
        print '\0034OTC Eauth Error: Decrypted message does not contain expected challenge string format.\003'
    return xchat.EAT_ALL
xchat.hook_command('ASKPW', askpw_cb, help="/ASKPW Ask user for gpg passphrase.")

def detect_eauth_challenge(word, word_eol, userdata):
    is_challenge = False
    if word[0] == ':gribble!~gribble@unaffiliated/nanotube/bot/gribble' and re.search('hostmask %s!' % (xchat.get_info('nick'),), word_eol[0]):
        challenge_url = word[-1]
        if challenge_url[:-16] == 'http://bitcoin-otc.com/otps/':
            xchat.challenge_data = urllib.urlopen(challenge_url).read()
            xchat.command('GETSTR "your gpg passphrase" ASKPW "Enter gpg passphrase"')
    return xchat.EAT_NONE

xchat.hook_server('PRIVMSG', detect_eauth_challenge)

def eauth_cb(word, word_eol, userdata):
    xchat.command('msg gribble ;;eauth ' + _otcnick)
    return xchat.EAT_ALL
xchat.hook_command('EAUTH', eauth_cb, help="/EAUTH Initiate auth procedure with gribble.")
