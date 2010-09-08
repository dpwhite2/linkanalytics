from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',
    (r'^create_target/$', 'views.createTrackedUrlTarget'),
    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    (r'^access/(?P<uuid>[a-f0-9]{32})/(?P<file>[-\w\d_./]+)/$', 'views.accessTrackedUrl'),
)