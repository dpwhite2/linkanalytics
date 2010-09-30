"""
    Tests for normal views as well as targetviews.
"""
import datetime

from linkanalytics.models import TrackedUrlInstance
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

#class CreateTrackedUrlTarget_TestCase(LinkAnalytics_DBTestCaseBase):
#    pass

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
        url = helpers.urlreverse_redirect_local(i.uuid, filepath='linkanalytics/testurl/')
        response = self.client.get(url, follow=True)
        chain = response.redirect_chain
        
        self.assertEquals(len(chain),1)
        self.assertEquals(chain[0],(u'http://testserver/linkanalytics/testurl/',302))
        
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
        url = helpers.urlreverse_redirect_http(uuid=i.uuid, domain='www.google.com')
        
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
    pass


#==============================================================================#



