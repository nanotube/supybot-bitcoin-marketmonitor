# Thanks to pnicholson for this script!

#
# If you are having problems with this script, try not using a PassPhrase for the gpg key !!
# 

using terms from application "Colloquy"
	
	# Your nickname on #bitcoin-otc
	property theNickname : "nick_name"
	# Your PGP key id
	property yourKeyid : "1234567876"
	
	
	## Configuration ends here ##
	property processGPG : 0
	property challengeResponse : "Request successful for user " & theNickname
	
	on process outgoing chat message theMessage
		set processGPG to 0
		set messageText to (get body of theMessage as string)
		
		if messageText contains ";;gpg eauth " & theNickname then
			set processGPG to 1
		end if
	end process outgoing chat message
	
	on process incoming chat message theMessage from theUser
		set messageText to (get HTML of theMessage as string)
		set userNick to (get name of theUser as string)
		
		if processGPG is 1 and userNick is "gribble" and messageText contains challengeResponse then
			set processGPG to 0
			#with timeout of 10 seconds
			set gpgToken to (do shell script "curl 'http://bitcoin-otc.com/otps/" & yourKeyid & "' | gpg --no-tty -d")
			#end timeout
			tell (display direct chat panel for theUser)
				send message ";;gpg everify " & gpgToken
			end tell
			
		end if
	end process incoming chat message
end using terms from

on run
	display dialog "Don't run me, move me to ~/Library/Application Support/Colloquy/PlugIns/
			and type /reload plugins in Colloquy."
end run
