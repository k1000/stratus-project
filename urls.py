from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'stratusproject.views.home', name='home'),
    # url(r'^stratusproject/', include('stratusproject.foo.urls')),

    # Uncomment thedd admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/git/', include('stratus.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^chat/', include('chat.urls')),
)

urlpatterns += staticfiles_urlpatterns()

"""
if settings.DEBUG:
    import tornado, os

    urlpatterns += patterns('',    
        (r"^static/stratus/(.*)", tornado.web.StaticFileHandler, {"path": "/home/kam/Projects/stratus/stratus-project/static/stratus/"}),
    )
"""