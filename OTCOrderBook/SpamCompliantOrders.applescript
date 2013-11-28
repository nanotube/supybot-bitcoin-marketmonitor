# Thanks to TheButterZone (1BUTRZ85L1JuoX5y2XRjxJaYcjcMLhPJcY) for this script!
# This works under OSX 10.6.8, Adium 1.5.*
# In Adium, you need to set your Freenode account options to run at least this command on connect: /join #bitcoin-otc
# There are 2 fields you need to replace:
# 1) #####, with your order number
# 2) The number after each delay. 21600 is the number of seconds in 6 hours. 28800 is the number of seconds in 8 hours.
# 21600: your order will show 4 times in a 24 hour day. 28800: your order will show 3 times in a 24 hour day.
# You will be in compliance and not accused of or penalized for spamming, as 3-4 offers per day are in
# full compliance with http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc#No_spam_policy
# Once you edit this script to your unique specs, save it as a run-only application.
# Only run this when Adium is already logged into Freenode.

	tell application "Adium"
		send the chat "#bitcoin-otc" message ";;view #####"
		delay 21600
		send the chat "#bitcoin-otc" message ";;view #####"
		delay 21600
		send the chat "#bitcoin-otc" message ";;view #####"
		delay 21600
		send the chat "#bitcoin-otc" message ";;view #####"
	end tell
