"""
    Tests for normal views as well as targetviews.
"""
import datetime
import imghdr

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import TrackedInstance, Visitor
from linkanalytics import targetviews, urlex

import base

#==============================================================================#
# View tests:

class AccessHashedUrl_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_hashValidation(self):        
        t = self.new_tracker(name='Name1')
        v = self.new_visitor(username='trackee1')
        i = t.add_visitor(v)
        
        # This first try will contain a hash calculated for a different url.
        hash = urlex.generate_urlhash(i.uuid, '/linkanalytics/nonexistent_url/')
        urltail = urlex.urltail_redirect_local('linkanalytics/testurl/')
        url = urlex.assemble_hashedurl(hash, i.uuid, urltail)
        # This should not pass the hash checker
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, 404)
        
        url = urlex.hashedurl_redirect_local(i.uuid, 'linkanalytics/testurl/')
        # This now should pass the hash checker
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.redirect_chain),1)
        

class CreateTrackedUrl_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

class CreateTrackee_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass


#==============================================================================#
# Target View tests:

class ViewRedirect_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_local_redirect(self):
        t = self.new_tracker('url1')
        v = self.new_visitor('trackee1')
        i = t.add_visitor(v)
        
        url = urlex.hashedurl_redirect_local(i.uuid, 'linkanalytics/testurl/')
        response = self.client.get(url, follow=True)
        chain = response.redirect_chain
        
        self.assertEquals(len(chain), 1)
        self.assertEquals(chain[0],
                          (u'http://testserver/linkanalytics/testurl/',302))
        
        # reload the instance so its fields represent its current state
        i = TrackedInstance.objects.filter(uuid=i.uuid)[0]
        
        self.assertEquals(i.first_access.date(), datetime.date.today())
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.access_count, 1)
        
    def test_nonlocal_redirect(self):
        t = self.new_tracker('url1')
        v = self.new_visitor('trackee1')
        i = t.add_visitor(v)
        
        url = urlex.hashedurl_redirect_http(i.uuid, domain='www.google.com')
        
        # Limitation of Django testing framework: non-local urls will not be 
        # accessed.  So, in this case, www.google.com is NOT actually accessed.  
        # Instead, a 404 error is produced.  This code tests that the url was 
        # correct, not that it was accessed.
        
        # This uses a custom view function to handle 404 errors.  So, there may 
        # be differences from what Django would return by default.
        response = self.client.get(url, follow=True)
        chain = response.redirect_chain
        
        self.assertEquals(len(chain), 1)
        self.assertEquals(chain[0], (u'http://www.google.com/', 302))
        
        # reload the instance so its fields represent its current state
        i = TrackedInstance.objects.filter(uuid=i.uuid)[0]
        
        self.assertEquals(i.first_access.date(), datetime.date.today())
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.access_count, 1)


class ViewHtml_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_email_receiptThankYou(self):
        t = self.new_tracker('url1')
        v = self.new_visitor('trackee1')
        i = t.add_visitor(v)
        
        path = 'email/access-thankyou.html'
        
        # make sure it can be accessed via the tracked url
        url = urlex.hashedurl_html(i.uuid, path)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        

class ViewPixelGif_TestCase(base.LinkAnalytics_DBTestCaseBase):
    pass

class ViewPixelPng_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        t = self.new_tracker('url1')
        v = self.new_visitor('trackee1')
        i = t.add_visitor(v)
        
        url = urlex.hashedurl_pixelpng(i.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        # In imghdr.what(), the first arg (the filename) is ignored when the 
        # 'h' arg (a byte stream) is given.
        self.assertEquals(imghdr.what('', h=response.content), 'png')


#==============================================================================#



