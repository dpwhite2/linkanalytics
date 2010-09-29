from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',

    (r'^email/compose/$', 'views.composeEmail'),
    (r'^email/compose/(?P<emailid>\d+)/$', 'views.composeEmail'),
    
    
    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional.
    (r'^access/(?P<uuid>[a-f0-9]{32})/(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)$', 'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
)
