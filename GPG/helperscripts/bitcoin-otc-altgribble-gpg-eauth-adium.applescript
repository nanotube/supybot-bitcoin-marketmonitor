# Thanks to TheButterZone (1BUTRZ85L1JuoX5y2XRjxJaYcjcMLhPJcY) for this script!
# This works under OSX 10.6.8-10.9, Adium 1.5.*, MacGPG2 2.0.*
# In Adium, you need to set your Freenode account options to run at least this command on connect: /join #bitcoin-otc
# There are 2 fields you need to replace: 
# YOURNICKGOESHERE, YOUR16DIGITGPGKEYIDGOESHERE
# "delay 30" is there to allow you time to type your GPG passphrase at the prompt and hit return. Hands off keyboard & mouse after you do that.
# Once you edit this script to your unique specs, save it as a run-only application.
# This will not work if altgribble is lagging and doesn't generate a new OTP before the event that decrypts it. Increase delay '5' (seconds) if you don't mind waiting longer.
# If Terminal prompts because of running processes on quit, change Terminal Shell settings to Prompt before closing: *Never
# Only run this when Adium is already logged into Freenode.

tell application "Adium"
  send the chat "#bitcoin-otc" message "/msg altgribble eauth YOURNICKGOESHERE"
end tell
delay 5
tell application "Terminal"
	do script "curl http://eauth.thetechgeek.org/YOUR16DIGITGPGKEYIDGOESHERE | gpg -d | pbcopy"
	delay 30
	quit
end tell
tell application "Adium"
	activate
	tell application "System Events"
		tell process "Adium"
			keystroke "/msg altgribble everify "
			delay 0.1
			key down {command}
			delay 0.2
			key code 9
			key up {command}
			delay 0.1
			keystroke return
			delay 1
			keystroke "/msg altgribble voiceme"
			keystroke return
		end tell
	end tell
end tell
