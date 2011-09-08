import simplejson
import time
import redis
import tornadio
#db = redis.Redis(host='localhost', port=6379, db=0)
from django.conf import settings

#https://github.com/gabrielfalcao/tornadio-chat/blob/master/app/server.py
#http://djay.posterous.com/how-to-make-a-realtime-chat-app-using-tornado-0

CHANNELS = {}
#
class Channel(object) :

    def __init__(self, ) :
        self._messages = []
        self._callbacks = []

    def message(self, type, nick, msg="") :
        m = { 'type': type, 'timestamp' : int(time.time()), 'text' : msg, 'nick' : nick }

        for cb in self._callbacks :
            cb([m])
        self._callbacks = []

        self._messages.append(m)

    def query(self, cb, since) :
        msgs = [m for m in self._messages if m['timestamp'] > since]
        if msgs :
            return cb(msgs)
        self._callbacks.append(cb)

    def size(self) :
        return 1024


def get_channel(name):
    if name not in CHANNELS.keys():
        CHANNELS[name]=Channel()
    
    return CHANNELS.get( name )
         
class ChatConnection(tornadio.SocketConnection):
    # Class level variable
    participants = {}
    nick = ""
    room = ""

    def on_open(self, *args, **kwargs):
        pass
        # send participants in the room
        #self.send("{text:'Welcome!'}")

    def on_message(self, message):
        #msg = simplejson.load( message )
        but_me=False

        nick = message.get("nick")

        # join or rejoin 
        if nick not in self.participants or self.participants.get(nick) is not self:
            message = self.join( message )
        
        if "timestamp" not in message:
            message["timestamp"] = int(time.time())

        if settings.DEBUG:
            print self.participants.keys()
            print message

        self.broadcast( message, self.room, but_me )
    
    def broadcast(self, msg, room=None, but_me=False):
        participants = self.participants
        if but_me:
            del participants[ self.nick ]
        #send_to = filter(lambda p: not p.is_closed, participants.values())
        send_to = participants.values()

        if room:
            send_to = filter(lambda p: p.room is room, send_to)
            channel = get_channel(room)
            channel.message( msg.get("type"), msg.get("nick"), msg.get("msg") )
            
        if settings.DEBUG:
            print send_to
        
        map(lambda p: p.send(msg), self.participants.values())
    
    def send_private( self, msg, to):
        self.participants[to].send(msg)
    
    def join( self, msg):
        self.nick = msg.get("nick")
        self.room = msg.get("room")
        self.participants[self.nick] = self
        msg.update(dict(
            msg = "%s joined" % self.nick,
            type = "info"
        ))
        
        channel = get_channel(self.room)
        self.send( {"messages":channel._messages} )
        return msg

    def on_close(self):
        del self.participants[self.nick]
        self.broadcast( "A user %s has left." % self.nick, self.room )

    @classmethod
    def who(cls) :
        return [ s.nick for s in self.participants ]



#use the routes classmethod to build the correct resource
ChatRouter = tornadio.get_router(ChatConnection)