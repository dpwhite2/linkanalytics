"""
    Tests for normal views as well as targetviews.
"""
import datetime
import imghdr

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import TrackedUrlInstance, Email, DraftEmail, Trackee
from linkanalytics import targetviews
import helpers
import base

#==============================================================================#
# View tests:

class AccessTrackedUrl_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

class CreateTrackedUrl_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

class CreateTrackee_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

#==============================================================================#
# Email view tests:

class ViewEmailMain_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    def test_contacts_count(self):
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no trackees
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 0)
            
            # Case 2: one trackee with an email
            t = Trackee(username='withemail', emailaddress='user0@example.com')
            t.save()
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 1)
            
            # Case 3: one trackee with and one without an email
            t = Trackee(username='withoutemail')
            t.save()
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 1)
            
    def test_draft_count(self):
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no drafts
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 0)
            
            # Case 2: one unsent draft
            e = DraftEmail()
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 1)
            
            # Case 3: first two unsent drafts, then one unsent draft and one 
            #         sent draft
            e = DraftEmail()
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 2)
            e.sent = True
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 1)
            
    def test_sent_count(self):
        u = self.new_trackedurl('trackedurl')
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no emails
            response = self.client.get(url)
            self.assertEquals(response.context['sent_count'], 0)
            
            # Case 2: one sent email
            e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['sent_count'], 1)
        
    
class ComposeEmail_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    def test_basic_edit(self):
        # Very basic test... just see that url exists.
        e = DraftEmail()
        e.save()
        id = e.pk
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-idcompose', 
                             kwargs={'emailid':id})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
    
class ViewSentEmails_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewsent')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
    
class ViewDraftEmails_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewdrafts')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
    
class ViewEmailRead_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        u = self.new_trackedurl('trackedurl')
        e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
        e.save()
        id = e.pk
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewread', 
                             kwargs={'emailid': id})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)

#==============================================================================#
# Target View tests:

class ViewRedirect_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_local_redirect(self):
        u = self.new_trackedurl('url1')
        t = self.new_trackee('trackee1')
        i = u.add_trackee(t)
        
        # The url we are resolving, using the default urls.py and targeturls.py:
        #   URLINSTANCE  TARGETVIEW
        #   URLINSTANCE = /linkanalytics/access/{uuid}
        #   TARGETVIEW =  /r/linkanalytics/testurl/
        url = helpers.urlreverse_redirect_local(i.uuid, 
                                              filepath='linkanalytics/testurl/')
        response = self.client.get(url, follow=True)
        chain = response.redirect_chain
        
        self.assertEquals(len(chain),1)
        self.assertEquals(chain[0],
                          (u'http://testserver/linkanalytics/testurl/',302))
        
        # reload the instance so its fields represent its current state
        i = TrackedUrlInstance.objects.filter(uuid=i.uuid)[0]
        
        self.assertEquals(i.first_access.date(), datetime.date.today())
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.access_count, 1)
        
    def test_nonlocal_redirect(self):
        u = self.new_trackedurl('url1')
        t = self.new_trackee('trackee1')
        i = u.add_trackee(t)
        
        # The url we are resolving, using the default urls.py and targeturls.py:
        #   URLINSTANCE  TARGETVIEW
        #   URLINSTANCE = /linkanalytics/access/{uuid}
        #   TARGETVIEW =  /http/www.google.com/       
        url = helpers.urlreverse_redirect_http(uuid=i.uuid, 
                                               domain='www.google.com')
        
        # Limitation of Django testing framework: non-local urls will not be 
        # accessed.  So, in this case, www.google.com is NOT actually accessed.  
        # Instead, a 404 error is produced.  This code tests that the url was 
        # correct, not that it was accessed.
        
        # This uses a custom view function to handle 404 errors.  So, there may 
        # be differences from what Django would return by default.
        response = self.client.get(url, follow=True)
        chain = response.redirect_chain
        
        self.assertEquals(len(chain),1)
        self.assertEquals(chain[0],(u'http://www.google.com/',302))
        
        # reload the instance so its fields represent its current state
        i = TrackedUrlInstance.objects.filter(uuid=i.uuid)[0]
        
        self.assertEquals(i.first_access.date(), datetime.date.today())
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.access_count, 1)


class ViewHtml_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_email_receiptThankYou(self):
        u = self.new_trackedurl('url1')
        t = self.new_trackee('trackee1')
        i = u.add_trackee(t)
        
        path = 'email/access-thankyou.html'
        
        # make sure it can be accessed via the tracked url
        url = helpers.urlreverse_targetview_html(i.uuid, path)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        

class ViewPixelGif_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

class ViewPixelPng_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        u = self.new_trackedurl('url1')
        t = self.new_trackee('trackee1')
        i = u.add_trackee(t)
        
        url = helpers.urlreverse_targetview_pixelpng(i.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        # In imghdr.what(), the first arg (the filename) is ignored when the 
        # 'h' arg (a byte stream) is given.
        self.assertEquals(imghdr.what('',h=response.content), 'png')


#==============================================================================#



