from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
import json
import time 
import tornado.web
from django_tornado.decorator import asynchronous

#
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
#
#
class ChatResponseError(HttpResponse) :
    def __init__(self, message) :
        super(ChatResponseError, self).__init__(status=400, content=json.dumps({ 'error' : message }))

class ChatResponse(HttpResponse) :
    def __init__(self, data) :
        super(ChatResponse, self).__init__(content=json.dumps(data))

#
#
#
def index(request) :
    return render_to_response('chat/index.html')

def clientjs(request) :
    return render_to_response('chat/client.js')

def join(request) :
    nick = request.GET['nick']

    if not nick :
        return ChatResponseError("Bad nickname")
    
    session = Session(nick)
    
    room_name = request.GET.get("room")
    channel = get_channel(room_name)
    channel.message('join', nick, "%s joined" % nick)

    return ChatResponse({ 
                    'id' : session.id,
                    'nick': session.nick,
                    'rss': channel.size(), 
                    'starttime': int(time.time()),
            })

def part(request ) :
    id = request.GET['id']

    session = Session.get(id)
    if not session :
        return ChatResponseError('session expired')
    
    room_name = request.GET.get("room")
    channel = get_channel(room_name)
    channel.message('part', session.nick)

    Session.remove(id)
    
    return ChatResponse({ 'rss': 0 })

def send(request) :
    id = request.GET['id']
    session = Session.get(id)
    if not session :
        return ChatResponseError('session expired')
    
    room_name = request.GET.get("room")
    channel = get_channel(room_name)
    channel.message('msg', session.nick, request.GET['text'])

    return ChatResponse({ 'rss' : channel.size() })

def who(request) :
    room_name = request.GET.get("room")
    channel = get_channel(room_name)
    return ChatResponse({ 'nicks': Session.who(), 'rss' : channel.size() })

@asynchronous
def recv(request, handler, ) :
    response = {}
    
    room_name = request.GET.get("room")
    channel = get_channel(room_name)
    
    if 'since' not in request.GET :
        return ChatResponseError('Must supply since parameter')
    if 'id' not in request.GET :
        return ChatResponseError('Must supply id parameter')

    id = request.GET['id']
    session = Session.get(id)
    if session :
        session.poke()

    since = int(request.GET['since'])
    
    def on_new_messages(messages) :
        if handler.request.connection.stream.closed():
            return
        handler.finish({ 'messages': messages, 'rss' : channel.size() })

    channel.query(handler.async_callback(on_new_messages), since)
