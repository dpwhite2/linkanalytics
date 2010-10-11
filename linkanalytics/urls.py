from django.conf.urls.defaults import *

# Note that the trailing slash in _TAILPATH is optional.
_TAILPATH = r'(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)'
_UUID = r'(?P<uuid>[a-f0-9]{32})'
# The hash can be many lengths depending on the exact algorithm used, so only a 
# lower bound is given.
_HASH = r'(?P<hash>[a-f0-9]{32,})'

urlpatterns = patterns('linkanalytics',
    
    (r'^email/', include('linkanalytics.email.urls')),

    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    
    # The Regex for accessTrackedUrl and accessHashedTrackedUrl: the ending '/' 
    # is optional.
    (r'^access/'+_UUID+r'/'+_TAILPATH+r'$', 
        'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
    (r'^access/j/'+_HASH+r'/'+_UUID+r'/'+_TAILPATH+r'$', 
        'views.accessHashedTrackedUrl', {}, 'linkanalytics-accesshashedview'),
)
