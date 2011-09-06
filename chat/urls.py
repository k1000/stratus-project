from django.conf.urls.defaults import *

urlpatterns = patterns('chat.views',
    url(r'^$', 'index'),
    url(r'^client.js$', 'clientjs'),
    url(r'^join', 'join'),
    url(r'^recv', 'recv'),
    url(r'^send', 'send'),
    url(r'^who', 'who'),
)
