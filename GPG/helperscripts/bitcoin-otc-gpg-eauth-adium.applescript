# Thanks to TheButterZone (1TBZYXjrGjXCEN1SprpF66Jzy5uN3GiLS) for this script!
# This works under OSX 10.6.8, Adium 1.5.*, MacGPG2 2.0.17-9
# In Adium, you need to set your Freenode account options to run at least this command on connect: /join #bitcoin-otc
# There are 2 fields you need to replace: 
# YOURNICKGOESHERE, YOURGPGKEYIDGOESHERE
# "delay 30" is there to allow you time to type your GPG passphrase in the prompt and hit return. Hands off keyboard & mouse after you do that.
# Once you edit this script to your unique specs, save it as a run-only application.
# This will not work if gribble is lagging and doesn't generate a new OTP before the event that decrypts it. Increase delay '5' (seconds) if you don't mind waiting longer.
# If Terminal prompts because of running processes on quit, change Terminal Shell settings to Prompt before closing: *Never
# Only run this when Adium is already logged into Freenode.

tell application "Adium"
  send the chat "#bitcoin-otc" message "/msg gribble gpg eauth YOURNICKGOESHERE"
end tell
delay 5
tell application "Terminal"
	do script "curl http://bitcoin-otc.com/otps/YOURGPGKEYIDGOESHERE | gpg -d | pbcopy"
	delay 30
	tell application "Adium"
		activate
		tell application "System Events"
			keystroke "/msg gribble gpg everify "
		end tell
		delay 0.1
		tell application "System Events"
			keystroke "v" using {command down}
		end tell
		delay 0.1
		tell application "System Events"
			keystroke return
		end tell
		delay 0.1
		tell application "System Events"
			keystroke "/msg gribble voiceme"
		end tell
		tell application "System Events"
			keystroke return
		end tell
	end tell
	delay 25
	tell application "Terminal"
		quit
	end tell
end tell
