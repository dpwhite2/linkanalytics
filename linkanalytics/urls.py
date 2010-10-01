from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics',

    (r'^email/$', 'views.viewEmail', {}, 'linkanalytics-email-main'),
    
    (r'^email/compose/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-compose'),
    (r'^email/compose/(?P<emailid>\d+)/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-idcompose'),
    
    (r'^email/viewsent/$', 'views.viewSentEmails', 
                    {}, 'linkanalytics-email-viewsent'),
    (r'^email/viewdrafts/$', 'views.viewDraftEmails', 
                    {}, 'linkanalytics-email-viewdrafts'),
    (r'^email/contacts/$', 'views.viewEmailContacts', 
                    {}, 'linkanalytics-email-viewcontacts'),
    
    (r'^email/(?P<emailid>\d+)/$', 'views.viewSingleSentEmail', 
                    {}, 'linkanalytics-email-viewsingle'),
    (r'^email/(?P<emailid>\d+)/read/$', 'views.viewEmailReadList', 
                    {}, 'linkanalytics-email-viewread'),
    (r'^email/(?P<emailid>\d+)/unread/$', 'views.viewEmailUnreadList', 
                    {}, 'linkanalytics-email-viewunread'),
    (r'^email/(?P<emailid>\d+)/recipients/$', 'views.viewEmailRecipientsList', 
                    {}, 'linkanalytics-email-viewrecipients'),
    (r'^email/(?P<emailid>\d+)/content/$', 'views.viewSentEmailContent', 
                    {}, 'linkanalytics-email-viewsentcontent'),
    
    (r'^create_trackee/$', 'views.createTrackee'),
    (r'^create_trackedurl/$', 'views.createTrackedUrl'),
    # The Regex for accessTrackedUrl: the ending '/' is optional.
    (r'^access/(?P<uuid>[a-f0-9]{32})/(?P<tailpath>(?:(?:/[-\w\d_.])|[-\w\d_.])+/?)$', 
                    'views.accessTrackedUrl', {}, 'linkanalytics-accessview'),
)
