from django.conf.urls.defaults import *

urlpatterns = patterns('linkanalytics.email',

    (r'^$', 'views.viewEmail', {}, 'linkanalytics-email-main'),
    
    # Compose
    (r'^compose/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-compose'),
    (r'^compose/(?P<emailid>\d+)/$', 'views.composeEmail', 
                    {}, 'linkanalytics-email-idcompose'),
    
    # Main views (accessible in main menu).  Also includes Compose email view.
    (r'^viewsent/$', 'views.viewSentEmails', 
                    {}, 'linkanalytics-email-viewsent'),
    (r'^viewdrafts/$', 'views.viewDraftEmails', 
                    {}, 'linkanalytics-email-viewdrafts'),
    (r'^contacts/$', 'views.viewEmailContacts', 
                    {}, 'linkanalytics-email-viewcontacts'),
    (r'^headers_footers/$', 'views.editEmailHeadersFooters', 
                    {}, 'linkanalytics-email-headersfooters'),
                    
    # Create/edit contacts
    (r'^create_contact/$', 'views.createEmailContact', 
                    {}, 'linkanalytics-email-createcontact'),
    (r'^create_contact/(?P<username>[-_\d\w]+)$', 'views.createEmailContact', 
                    {}, 'linkanalytics-email-editcontact'),
    
    # Information about sent emails
    (r'^(?P<emailid>\d+)/$', 'views.viewSingleSentEmail', 
                    {}, 'linkanalytics-email-viewsingle'),
    (r'^(?P<emailid>\d+)/read/$', 'views.viewEmailReadList', 
                    {}, 'linkanalytics-email-viewread'),
    (r'^(?P<emailid>\d+)/unread/$', 'views.viewEmailUnreadList', 
                    {}, 'linkanalytics-email-viewunread'),
    (r'^(?P<emailid>\d+)/recipients/$', 'views.viewEmailRecipientsList', 
                    {}, 'linkanalytics-email-viewrecipients'),
    (r'^(?P<emailid>\d+)/content/$', 'views.viewSentEmailContent', 
                    {}, 'linkanalytics-email-viewsentcontent'),
                    
    
)