from django.conf.urls.defaults import *

# No trailing '/' in FILEPATH, although it may contain '/'.
FILEPATH = r'(?P<filepath>(?:(?:/[-\w\d_.])|[-\w\d_.])+)'

# Trailing '/' is allowed in PATH.
PATH = r'(?P<filepath>[-\w\d_./]+)'

# Domain: (SLD.)+ TLD (:port)?    -- TLD is .com, .org, .uk, etc
DOMAIN = r'(?P<domain>([-\w\d]+\.)+[-\w\d]+(:\d+)?)'

#==============================================================================#
urlpatterns = patterns('linkanalytics.email',

    (r'^render/$', 'targetviews.targetview_renderemail', 
                                    {}, 'targetview-email-render'),
                                    
    (r'^acknowledge-receipt/$', 'targetviews.targetview_acknowledge', 
                                    {}, 'targetview-email-acknowledge'),
)

#==============================================================================#