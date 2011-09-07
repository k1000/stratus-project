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

class Session(object) :
    SESSIONS = {}
    CUR_ID  = 100

    def __init__(self, nick) :
        user_has_session = False
        for v in self.SESSIONS.values() :
            if v.nick == nick :
                #raise "In use"
                self.id = v.id
                self.nick = nick
                user_has_session = True

        if not user_has_session:
            self.nick = nick
            Session.CUR_ID += 1
            self.id   = Session.CUR_ID 

            Session.SESSIONS[str(self.id)] = self

    def poke(self) :
        pass

    @classmethod
    def who(cls) :
        return [ s.nick for s in Session.SESSIONS.values() ]

    @classmethod
    def get(cls, id) :
        return Session.SESSIONS.get(str(id), None)

    @classmethod
    def remove(cls, id) :
        if id in cls.SESSIONS :
            del Session.SESSIONS[id]


def get_channel(name):
    if name not in CHANNELS.keys():
        CHANNELS[name]=Channel()
    
    return CHANNELS.get( name )
    

                                  

class ChatConnection(tornadio.SocketConnection):
    # Class level variable
    participants = set()

    def on_open(self, *args, **kwargs):
        self.participants.add(self)
        # send participants in the room
        #self.send("{text:'Welcome!'}")

    def on_message(self, message):
        #msg = simplejson.load( message )
        if settings.DEBUG:
            print message

        if "join" in message:
            self.join( message )
            

        message["timestamp"] = int(time.time())
        for p in self.participants:
            p.send(message)

    def on_close(self):
        self.participants.remove(self)
        for p in self.participants:
            p.send("A user has left.")

    def join(self, request) :
        nick = request.get('nick')
        
        session = Session(nick)
        
        room_name = request.get("room")
        channel = get_channel(room_name)
        channel.message('join', nick, "%s joined" % nick)

        self.send({ 
            'id' : session.id,
            'nick': session.nick,
            'rss': channel.size(), 
            'starttime': int(time.time()),
        })

    def part(self, request ) :
        id = request.get('id')

        session = Session.get(id)
        if not session :
            return ChatResponseError('session expired')
        
        room_name = request.GET.get("room")
        channel = get_channel(room_name)
        channel.message('part', session.nick)

        Session.remove(id)
        
        self.send({ 'rss': 0 })

    def send__(self, request) :
        id = request.get('id')
        session = Session.get(id)

        room_name = request.get("room")
        channel = get_channel(room_name)
        channel.message('msg', session.nick, request.get('text'))

        self.send({ 'rss' : channel.size() })

    def who(self, room_name) :
        channel = get_channel(room_name)
        self.send({ 'nicks': Session.who(), 'rss' : channel.size() })



#use the routes classmethod to build the correct resource
ChatRouter = tornadio.get_router(ChatConnection)