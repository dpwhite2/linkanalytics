"""
Duplicate of the default urlconf in urls.py.  This allows urls to be customized 
without breaking tests.  It also allows some extra views to be used for testing 
only.
"""
# NOTE: Make sure this module stays synchronized with urls.py.

# Disable Nose test autodiscovery for this module.
__test__ = False

from django.conf.urls.defaults import *

import linkanalytics.urlsaccess

# Note that the trailing slash in _TAILPATH is optional.
_TAILPATH = r'(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)'
_UUID = r'(?P<uuid>[a-f0-9]{32})'
# The hash can be many lengths depending on the exact algorithm used, so only a 
# lower bound is given.
_HASH = r'(?P<hash>[a-f0-9]{32,})'


PREFIX = r'^linkanalytics/'

#==============================================================================#
urlpatterns = patterns('',
    
    #(PREFIX+r'email/', include('linkanalytics.email.urls')),

    #(PREFIX+r'create_trackee/$', 'views.createTrackee'),
    #(PREFIX+r'create_trackedurl/$', 'views.createTrackedUrl'),
    
    linkanalytics.urlsaccess.URLCONF_TUPLE,
    
    (r'^linkanalytics/', include('linkanalytics.urls')),
    
    # Some urls defined for testing purposes only.
    (PREFIX+r'testurl/$', 'linkanalytics.tests.test_views.testview'),
)

#==============================================================================#
handler404 = 'linkanalytics.tests.test_views.on_page_not_found'

