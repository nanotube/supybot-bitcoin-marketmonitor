require 'xmlrpc/client'

# Sign it
response = ""
STDOUT.sync = true
IO.popen("echo " + ARGV[0] + " | gpg --clearsign --cipher-algo AES256") do |pipe|
  pipe.sync = true
  while str = pipe.gets
    response += str
  end
end

# Post it
server = XMLRPC::Client.new2("http://paste.pocoo.org/xmlrpc/")
pasteid = server.call("pastes.newPaste",'text',response)
puts 'http://paste.pocoo.org/raw/' + pasteid
