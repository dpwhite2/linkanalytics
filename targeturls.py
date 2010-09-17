from django.conf.urls.defaults import *

# No trailing '/' in FILEPATH, although it may contain '/'.
FILEPATH = r'(?P<filepath>(?:(?:/[-\w\d_.])|[-\w\d_.])+)'

# Trailing '/' is allowed in PATH.
PATH = r'(?P<filepath>[-\w\d_./]+)'

# Domain: (SLD.)+ TLD (:port)?    -- TLD is .com, .org, .uk, etc
DOMAIN = r'(?P<domain>([-\w\d]+\.)+[-\w\d]+(:\d+)?)'

urlpatterns = patterns('linkanalytics',
    # FILEPATH in http and https is optional.
    (r'^http/'+DOMAIN+r'(?:/'+PATH+r')?/?$', 'targetviews.targetview_redirect', {'scheme':'http'}),
    (r'^https/'+DOMAIN+r'(?:/'+PATH+r')?/?$', 'targetviews.targetview_redirect', {'scheme':'https'}),
    (r'^r/'+PATH+r'/?$', 'targetviews.targetview_redirect'),
    (r'^h/'+FILEPATH+r'/?$', 'targetviews.targetview_html'),
    (r'^pxg/?$', 'targetviews.targetview_pixelgif'),
    (r'^pxp/?$', 'targetviews.targetview_pixelpng'),
)

