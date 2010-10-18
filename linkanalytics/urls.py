from django.conf.urls.defaults import *

#==============================================================================#
# Note that the trailing slash in _TAILPATH is optional.
_TAILPATH = r'(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)'
_UUID = r'(?P<uuid>[a-f0-9]{32})'
# The hash can be many lengths depending on the exact algorithm used, so only a 
# lower bound is given.
_HASH = r'(?P<hash>[a-f0-9]{32,})'

#==============================================================================#
# The following variables are used by target views.

# No trailing '/' in FILEPATH, although it may contain '/'.
FILEPATH = r'(?P<filepath>(?:(?:/[-\w\d_.])|[-\w\d_.])+)'

# Trailing '/' is allowed in PATH.
PATH = r'(?P<filepath>[-\w\d_./]+)'

# Domain: (SLD.)+ TLD (:port)?    -- TLD is .com, .org, .uk, etc
DOMAIN = r'(?P<domain>([-\w\d]+\.)+[-\w\d]+(:\d+)?)'

#==============================================================================#
urlpatterns = patterns('linkanalytics',
    
    (r'^email/', include('linkanalytics.email.urls')),

    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    
    # The Regex for accessTrackedUrl and accessHashedTrackedUrl: the ending '/' 
    # is optional.
    ##(r'^access/j/'+_HASH+r'/'+_UUID+r'/'+_TAILPATH+r'$', 
    ##    'views.accessHashedTrackedUrl', {}, 'linkanalytics-accesshashedview'),
    
    # Target views...
    (r'^http/'+DOMAIN+r'(?:/'+PATH+r')?/?$', 'targetviews.targetview_redirect', 
                                        {'scheme':'http'}, 'redirect-http'),
    (r'^https/'+DOMAIN+r'(?:/'+PATH+r')?/?$', 'targetviews.targetview_redirect', 
                                        {'scheme':'https'}, 'redirect-https'),
    (r'^r/'+PATH+r'/?$', 'targetviews.targetview_redirect', 
                                        {}, 'redirect-local'),
    
    (r'^h/'+FILEPATH+r'/?$', 'targetviews.targetview_html', 
                                        {}, 'targetview-html'),
    (r'^gpx/?$', 'targetviews.targetview_pixelgif', {}, 'targetview-pixelgif'),
    (r'^ppx/?$', 'targetviews.targetview_pixelpng', {}, 'targetview-pixelpng'),
)

#==============================================================================#

