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

    def message(self, type, nick, text="") :
        m = { 'type': type, 'timestamp' : int(time.time()), 'text' : text, 'nick' : nick }

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

        
class ChatConnection(tornadio.SocketConnection):
    # Class level variable
    participants = set()
    nick = ""
    room = ""

    def on_open(self, *args, **kwargs):
        self.participants.add(self)
        # send participants in the room
        #self.send("{text:'Welcome!'}")

    def on_message(self, message):
        #msg = simplejson.load( message )
        if settings.DEBUG:
            print message

        if "join" in message:
            self.nick = message.get("join")
            self.room = message.get("room")

        message["timestamp"] = int(time.time())
        self.broadcast( message, message.get("room") )

    def broadcast(self, msg, room=None):
        if room:
            for p in self.participants:
                if p.room == room:
                    p.send(msg)
        else:
            for p in self.participants:
                p.send(msg)

    def on_close(self):
        self.participants.remove(self)
        self.broadcast( "A user %s has left." % self.nick, self.room )

    @classmethod
    def who(cls) :
        return [ s.nick for s in self.participants ]



#use the routes classmethod to build the correct resource
ChatRouter = tornadio.get_router(ChatConnection)