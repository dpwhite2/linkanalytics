from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',

    (r'^email/$', 'views.viewEmail'),
    
    (r'^email/compose/$', 'views.composeEmail'),
    (r'^email/compose/(?P<emailid>\d+)/$', 'views.composeEmail'),
    
    (r'^email/viewsent/$', 'views.viewSentEmails'),
    (r'^email/viewdrafts/$', 'views.viewDraftEmails'),
    (r'^email/contacts/$', 'views.viewEmailContacts'),
    
    (r'^email/(?P<emailid>\d+)/$', 'views.viewSingleSentEmail'),
    (r'^email/(?P<emailid>\d+)/read/$', 'views.viewEmailReadList'),
    (r'^email/(?P<emailid>\d+)/unread/$', 'views.viewEmailUnreadList'),
    (r'^email/(?P<emailid>\d+)/recipients/$', 'views.viewEmailRecipientsList'),
    (r'^email/(?P<emailid>\d+)/content/$', 'views.viewSentEmailContent'),
    
    
    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional.
    (r'^access/(?P<uuid>[a-f0-9]{32})/(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)$', 'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
)
