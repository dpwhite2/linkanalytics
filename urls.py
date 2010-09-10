from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',
    (r'^create_target/$', 'views.createTrackedUrlTarget'),
    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional, but if it is present, it will NOT be included in <targetname>.
    (r'^access/(?P<uuid>[a-f0-9]{32})/(?P<targetname>(?:(?:/[-\w\d_.])|[-\w\d_.])+)/?$', 'views.accessTrackedUrl'),
)