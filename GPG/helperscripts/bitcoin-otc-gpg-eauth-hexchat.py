__module_name__ = "bitcoin-otc-gpg-eauth-hexchat"
__module_version__ = "0.0"
__module_description__ = "bitcoin-otc GPG eauth for Hexchat"

# Thanks to TheButterZone (191R9RaC4mUsc4mKAQPY1TBZc5JGRt13zp) & especially ______ () for this script!
# This will eventually work under Hexchat Linux
# There are 2 fields you need to replace: 
# YOURNICKGOESHERE, YOUR16DIGITGPGKEYIDGOESHERE
# time.sleep(30) (seconds) is there to allow you time to type your GPG passphrase at the prompt and hit return. Hands off keyboard & mouse after you do that.
# This will not work if gribble is lagging and doesn't generate a new OTP before the event that decrypts it. Increase time.sleep(5) (seconds) if you don't mind waiting longer.

hexchat.command("MSG /join #gribble")
time.sleep(2)
hexchat.command("MSG /msg gribble eauth YOURNICKGOESHERE")
time.sleep(5)
import requests
r = requests.get('http://bitcoin-otc.com/otps/YOUR16DIGITGPGKEYIDGOESHERE')

# I can't easily figure out how to pass OTP to gpg for decrypt and copy/paste to/from clipboard, not having Linux, Hexchat, or programmed Py before.

time.sleep(30)
hexchat.command("MSG /msg gribble everify (# decrypted OTP paste here)")
time.sleep(1)
hexchat.command("MSG /msg gribble voiceme")
time.sleep(2)
hexchat.command("MSG /join #bitcoin-otc")
hexchat.command("MSG /part #gribble")
