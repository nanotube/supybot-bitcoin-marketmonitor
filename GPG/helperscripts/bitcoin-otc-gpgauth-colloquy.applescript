# Thanks to M4v3R for this script!

# Your nickname on #bitcoin-otc
property theNickname : "YOUR_NICKNAME"

# Your passphrase
property gpgPassphrase : "YOUR_PASSPHRASE"

# Uncomment next line (and comment previous) if you want 
# to be asked for the passphrase every time you do the auth
# property gpgPassphrase : null

## Configuration ends here ##
property processGPG : 0
property challengeQuery : "Your challenge string is: "

using terms from application "Colloquy"
	on process outgoing chat message theMessage
		set processGPG to 0
		set messageText to (get body of theMessage as string)
		if messageText is ";;gpg auth " & theNickname then
			set processGPG to 1
		end if
	end process outgoing chat message
	
	on process incoming chat message theMessage from theUser
		set messageText to (get HTML of theMessage as string)
		set userNick to (get name of theUser as string)
		
		if processGPG is 1 and messageText contains challengeQuery and userNick is "gribble" then
			
			# Reset handler variable
			set processGPG to 0
			
			# Get challenge string
			set AppleScript's text item delimiters to challengeQuery
			set challengeHTML to text item 2 of messageText
			set challenge to (do shell script "echo " & quoted form of challengeHTML & "| sed 's/<[^>]*>//g'")
			
			# Get the passphrase
			if gpgPassphrase is null then
				set gpgPassphrase to text returned of (display dialog "Please enter your passphrase:" with title "GPG Auth" default answer "")
			end if
			
			# Get GPG signature
			set theFileID to open for access "/tmp/gpg-message" with write permission
			write challenge to theFileID
			close access theFileID
			tell application "Terminal"
				activate
				with timeout of 10 seconds
					do script with command "echo '" & gpgPassphrase & "' | gpg --clearsign --passphrase-fd 0 /tmp/gpg-message"
				end timeout
			end tell
			delay (3) # Give it some time...
			tell application "Terminal" to quit
			tell application "Colloquy" to activate
			set gpgSignature to (do shell script "cat /tmp/gpg-message.asc")
			do shell script "rm /tmp/gpg-message*"
			tell application "http://paste.pocoo.org/xmlrpc/" to call xmlrpc {method name:"pastes.newPaste", parameters:{"", gpgSignature}}
			set pasteURL to result
			
			# Send the message to channel
			tell active panel of front window
				send message ";;gpg verify http://paste.pocoo.org/raw/" & pasteURL & "/"
			end tell
		end if
	end process incoming chat message
end using terms from
on run
	if gpgPassphrase is null then
		display dialog "NULL"
	end if
end run