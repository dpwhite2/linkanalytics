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

urlpatterns = patterns('linkanalytics',

    (PREFIX+r'email/$', 'views.viewEmail', {}, 'linkanalytics-email-main'),
    
    (PREFIX+r'email/compose/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-compose'),
    (PREFIX+r'email/compose/(?P<emailid>\d+)/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-idcompose'),
    
    (PREFIX+r'email/viewsent/$', 'views.viewSentEmails', 
                    {}, 'linkanalytics-email-viewsent'),
    (PREFIX+r'email/viewdrafts/$', 'views.viewDraftEmails', 
                    {}, 'linkanalytics-email-viewdrafts'),
    (PREFIX+r'email/contacts/$', 'views.viewEmailContacts', 
                    {}, 'linkanalytics-email-viewcontacts'),
                    
    (PREFIX+r'email/create_contact/$', 'views.createEmailContact', 
                    {}, 'linkanalytics-email-createcontact'),
    (PREFIX+r'email/create_contact/(?P<username>[-_\d\w]+)$', 'views.createEmailContact',  
                    {}, 'linkanalytics-email-editcontact'),
    
    (PREFIX+r'email/(?P<emailid>\d+)/$', 'views.viewSingleSentEmail', 
                    {}, 'linkanalytics-email-viewsingle'),
    (PREFIX+r'email/(?P<emailid>\d+)/read/$', 'views.viewEmailReadList', 
                    {}, 'linkanalytics-email-viewread'),
    (PREFIX+r'email/(?P<emailid>\d+)/unread/$', 'views.viewEmailUnreadList', 
                    {}, 'linkanalytics-email-viewunread'),
    (PREFIX+r'email/(?P<emailid>\d+)/recipients/$', 'views.viewEmailRecipientsList', 
                    {}, 'linkanalytics-email-viewrecipients'),
    (PREFIX+r'email/(?P<emailid>\d+)/content/$', 'views.viewSentEmailContent', 
                    {}, 'linkanalytics-email-viewsentcontent'),
    
    
    (PREFIX+r'create_trackee/$', 'views.createTrackee'),
    (PREFIX+r'create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional.
    (PREFIX+r'access/(?P<uuid>[a-f0-9]{32})/'+_TAILPATH+'$', 
            'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
    # Some urls defined for testing purposes only.
    (PREFIX+r'testurl/$', 'tests.test_views.testview'),
    )
    
handler404 = 'linkanalytics.tests.test_views.on_page_not_found'