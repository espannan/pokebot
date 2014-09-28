import sys
import getopt
import socket
import string

# Make sure the correct number of arguments were entered
if len(sys.argv) != 3:
  print "Usage: pokebot.py <bot_nick> <channel>"
  sys.exit(2)


# All of the connection information
HOST="irc.freenode.net"
PORT=6667
NICK=sys.argv[1]
IDENT=NICK
REALNAME=NICK
CHANNEL=sys.argv[2]

# List of people in the room
NAMES=[]

# List of messages waiting to be shared
MESSAGES=[]

# connect to freenode
s=socket.socket()
s.connect((HOST,PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

# send a message to the channel
def sendmsg(chan, msg):
  s.send("PRIVMSG "+ chan +" :"+ msg +"\n")

def pickWeights(weight):
  message = "Bar + "

# remove the messages that have been delivered
def removeMessages(found):
  # if we start from the back, we won't fuck up the locations
  # in the list
  found.reverse()
  for i in found:
    del MESSAGES[i]

# check if the given nick has any messages in the queue
def checkMessages(nick):
  count=0
  found=[]
  for name,msg in MESSAGES:
    if name == nick:
      # remember the location of this message
      found.append(count)

      # post the message with the nick first
      msg= nick + ": " + msg
      sendmsg(CHANNEL,msg)

    count += 1

  # now that we've delivered messages, get rid of them
  removeMessages(found)

# used for stripping the : and @ symbols from around nicks
def stripGarbage(word):
  word = word.strip(':')
  word = word.strip('@')
  return word

# builds the NAMES list from the original login list
def buildNames(ircmsg):
  # when we join a room, the room info comes in two lines
  # the first line has the actual list 
  halves=ircmsg.split('\r\n')

  # split the line by spaces
  parts=halves[0].split(' ')

  # the names begin after the channel name
  i=parts.index(CHANNEL)
  i=i+1
  while i < len(parts):
    NAMES.append(stripGarbage(parts[i]))
    i+=1
  print NAMES

# add a newly joined nick to the list
def addName(ircmsg):
  # the nick of the person who joined is followed by the
  # '!' character, so we can just split the string by that
  parts=ircmsg.split('!')
  tempName = stripGarbage(parts[0])
  if tempName != NICK:
    checkMessages(tempName)
    NAMES.append(tempName)
  print(NAMES)

# remove a nick that has parted the room from the list
def removeName(ircmsg):
  parts=ircmsg.split('!')
  tempName = stripGarbage(parts[0])
  NAMES.remove(tempName)
  print(NAMES)

# lists everyone in the room in order to call their
# attention to the chat
def pingAll():
  msg = "ping "
  for i in NAMES:
    msg += i + " "
  sendmsg(CHANNEL, msg)

# saves a pairing of a message and the person it's 
# meant for in the MESSAGES list
def storeMsg(ircmsg):
  parts=ircmsg.split(' ')

  # the nick and message come right after "tell" in
  # the message
  i=parts.index("tell")+1
  nick=parts[i]
  i=i+1
  msg=""
  while i < len(parts):
    msg = msg + parts[i] + " "
    i = i + 1
  MESSAGES.append([nick,msg])
  print(MESSAGES)

# joins the given channel
def joinchan(chan):
  s.send("JOIN "+ chan +"\n")

# says Hello! to anyone who says hello to the bot
def hello():
  s.send("PRIVMSG "+ CHANNEL +" :Hello!\n")


###############################
#   LET'S START DOING STUFF
###############################

# join the channel
joinchan(CHANNEL)

# loop forever and check every message that IRC sends our way
while 1:
  # grab the latest message and remove trailing characters
  ircmsg = s.recv(2048)
  ircmsg = ircmsg.strip('\n\r')
  print(ircmsg)

  # if someone says "Hello pokebot" that we say hello back
  if ircmsg.find(":Hello "+ NICK) != -1:
    hello()

  # 353 is the code for when IRC provides the NAMES list, so 
  # at this point we can build our own list
  if ircmsg.find(" 353 "+ NICK) != -1:
    buildNames(ircmsg.split('353')[1])

  # if someone JOINs, we must add them to our NAMES list
  if ircmsg.find(" JOIN "+CHANNEL) != -1:
    addName(ircmsg)

  # if someone PARTs, we must remove them from our NAMES list
  if ircmsg.find(" PART "+CHANNEL) != -1:
    removeName(ircmsg)

  # if someone says "pokebot: ping *" then we ping the whole room
  if ircmsg.find(NICK+": ping") != -1:
    pingAll()

  # if someone says "pokebot: tell <nick> <message>", then we save
  # it to our MESSAGES list
  if ircmsg.find(NICK+": tell ") != -1:
    storeMsg(ircmsg)

  # if someone asks for help, print what you can do
  if ircmsg.find(NICK+": help") != -1:
    sendmsg(CHANNEL,"Usage:\n")
    sendmsg(CHANNEL,"Hello: I will say hello to you! [Hello pokebot]\n")
    sendmsg(CHANNEL,"Ping: I will get everyone's attention [pokebot: ping]\n")
    sendmsg(CHANNEL,"Messages: I can save messages for when someone joins the rooms [pokebot: tell panda007 you're awesomesauce]\n")

  # when the server pings us, we must respond appropriately
  if ircmsg.find("PING :") != -1: 
    s.send("PONG :Pong\n")
