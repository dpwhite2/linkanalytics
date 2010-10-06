"""
Duplicate of the default urlconf in urls.py.  This allows urls to be customized 
without breaking tests.  It also allows some extra views to be used for testing 
only.
"""
# NOTE: Make sure this module stays synchronized with urls.py.

# Disable Nose test autodiscovery for this module.
__test__ = False

from django.conf.urls.defaults import *




_TAILPATH = r'(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)'
PREFIX = r'^linkanalytics/'

from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',
    
    (PREFIX+r'email/', include('linkanalytics.email.urls')),

    (PREFIX+r'create_trackee/$', 'views.createTrackee'),
    (PREFIX+r'create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional.
    (PREFIX+r'access/(?P<uuid>[a-f0-9]{32})/(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)$', 
                    'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
    
    # Some urls defined for testing purposes only.
    (PREFIX+r'testurl/$', 'tests.test_views.testview'),
)

handler404 = 'linkanalytics.tests.test_views.on_page_not_found'

