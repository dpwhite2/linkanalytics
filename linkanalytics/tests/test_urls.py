"""
Duplicate of the default urlconf in urls.py.  This allows urls to be customized 
without breaking tests.  It also allows some extra views to be used for testing 
only.
"""
# NOTE: Make sure this module stays synchronized with urls.py.

# Disable Nose test autodiscovery for this module.
__test__ = False

from django.conf.urls.defaults import *

# Note that the trailing slash in _TAILPATH is optional.
_TAILPATH = r'(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)'
_UUID = r'(?P<uuid>[a-f0-9]{32})'
# The hash can be many lengths depending on the exact algorithm used, so only a 
# lower bound is given.
_HASH = r'(?P<hash>[a-f0-9]{32,})'


PREFIX = r'^linkanalytics/'

urlpatterns = patterns('linkanalytics',
    
    (PREFIX+r'email/', include('linkanalytics.email.urls')),

    (PREFIX+r'create_trackee/$', 'views.createTrackee'),
    (PREFIX+r'create_trackedurl/$', 'views.createTrackedUrl'),
    
    # The Regex for accessTrackedUrl and accessHashedTrackedUrl: the ending '/' 
    # is optional.
    ##(PREFIX+r'access/'+_UUID+r'/'+_TAILPATH+r'$', 
    ##    'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
    (PREFIX+r'access/j/'+_HASH+r'/'+_UUID+r'/'+_TAILPATH+r'$', 
        'views.accessHashedTrackedUrl', {}, 'linkanalytics-accesshashedview'),
    
    # Some urls defined for testing purposes only.
    (PREFIX+r'testurl/$', 'tests.test_views.testview'),
)

handler404 = 'linkanalytics.tests.test_views.on_page_not_found'

