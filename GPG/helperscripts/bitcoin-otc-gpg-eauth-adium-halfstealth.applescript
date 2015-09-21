# Thanks to TheButterZone (191R9RaC4mUsc4mKAQPY1TBZc5JGRt13zp) for this script!
# This works under OSX 10.6.8-10.10.3, Adium 1.5.*, MacGPG2 2.0.*
# There are 2 fields you need to replace: 
# YOURNICKGOESHERE, YOUR16DIGITGPGKEYIDGOESHERE
# "delay 30" is there to allow you time to type your GPG passphrase at the prompt and hit return. Hands off keyboard & mouse after you do that.
# Once you edit this script to your unique specs, save it as a run-only application.
# This will not work if gribble is lagging and doesn't generate a new OTP before the event that decrypts it. Increase delay '5' (seconds) if you don't mind waiting longer.
# If Terminal prompts because of running processes on quit, change Terminal Shell settings to Prompt before closing: *Never
# Only run this when Adium is already logged into Freenode.

tell application "Adium"
	activate
	send the active chat message "/join #gribble"
	delay 2
	send the active chat message "/msg gribble eauth YOURNICKGOESHERE"
end tell
delay 5
tell application "Terminal"
	do script "curl http://bitcoin-otc.com/otps/YOUR16DIGITGPGKEYIDGOESHERE | gpg2 -d | pbcopy"
	delay 30
	quit
end tell
tell application "System Events"
	tell process "Adium"
		keystroke "/msg gribble everify "
		delay 0.1
		key down {command}
		delay 0.2
		key code 9
		key up {command}
		delay 0.1
		keystroke return
		delay 1
		keystroke "/msg gribble voiceme"
		delay 2
		keystroke return
	end tell
	delay 2
	tell application "Adium"
		activate
		send the active chat message "/join #bitcoin-otc"
		send the active chat message "/join #bitcoin-pit"
		send the active chat message "/join #bitcoin-jobs"
		send the active chat message "/join #bitcoin-otc-ticker"
		send the active chat message "/join #bitcoin-otc-ratings"
		send the active chat message "/join #bitcoin"
		tell the chat "#gribble" to close
		delay 2
		tell the chat "bitcoin-otc" to open
	end tell
end tell
