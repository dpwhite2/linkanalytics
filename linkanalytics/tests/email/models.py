import datetime
import xml.etree.ElementTree

from django.db import IntegrityError
from django.core import mail as django_email
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, Trackee
from linkanalytics.email.models import DraftEmail, Email
from linkanalytics import app_settings
from linkanalytics import urlex

from .. import base


#==============================================================================#

class Email_TestCase(base.LinkAnalytics_DBTestCaseBase):
    # This class tests both the Email and DraftEmail classes
    def test_compile_basic(self):
        de = DraftEmail(fromemail='', subject='Subject')
        html = '<html><head></head><body></body></html>'
        de.message = html
        de.save()
        e = de._compile()
        
        self.assertEquals(e.subject, 'Subject')
        self.assertEquals(e.txtmsg, '')
        self.assertEqualsHtml(e.htmlmsg, html)
        
        # There's only one TrackedUrl object so far
        self.assertEquals(TrackedUrl.objects.count(), 1)
        self.assertEquals(e.trackedurl, TrackedUrl.objects.all()[0])
        
    def test_send_basic(self):
        """Sends an email to no one"""
        de = DraftEmail(fromemail='', subject='Subject')
        html = '<html><head></head><body></body></html>'
        de.message = html
        de.save()
        e = de.send()
        
        self.assertTrue(de.sent)
        self.assertEquals(e.subject, 'Subject')
        self.assertEquals(e.txtmsg, '')
        self.assertEqualsHtml(e.htmlmsg, html)
        
        # There's only one TrackedUrl object so far
        self.assertEquals(TrackedUrl.objects.count(), 1)
        self.assertEquals(e.trackedurl, TrackedUrl.objects.all()[0])
        
    def test_send_single(self):
        t = Trackee(username='user', emailaddress='user@example.com')
        t.save()
        de = DraftEmail(fromemail='', subject='Subject')
        html = '<html><head></head><body></body></html>'
        de.message = html
        de.save()
        de.pending_recipients.add(t)
        de.save()
        e = de.send()
        
        self.assertTrue(de.sent)
        self.assertEquals(e.subject, 'Subject')
        self.assertEquals(e.txtmsg, '')
        self.assertEqualsHtml(e.htmlmsg, html)
        
        # There's only one TrackedUrl object so far
        self.assertEquals(TrackedUrl.objects.count(), 1)
        self.assertEquals(e.trackedurl, TrackedUrl.objects.all()[0])
        
        self.assertEquals(len(django_email.outbox), 1)
        self.assertEquals(django_email.outbox[0].subject, 'Subject')
        self.assertEquals(django_email.outbox[0].recipients(), 
                          ['user@example.com'])
        
    def test_send_pixelimage(self):
        """Sends an email containing a pixelimage."""
        t = Trackee(username='user', emailaddress='user@example.com')
        t.save()
        html = '<html><head></head><body></body></html>'
        de = DraftEmail(fromemail='', subject='Subject')
        de.message = html
        de.pixelimage = True
        de.save()
        de.pending_recipients.add(t)
        de.save()
        eml = de.send()
        self.assertTrue(de.sent)
        
        qs = TrackedUrlInstance.objects.filter(trackee=t)
        self.assertEquals(qs.count(), 1)
        uuid = qs[0].uuid
        
        self.assertEquals(len(django_email.outbox), 1)
        msg = django_email.outbox[0]
        content,mime = msg.alternatives[0]
        self.assertEquals(mime, 'text/html')
        ##print '\n{0}\n'.format(content)
            
        e = xml.etree.ElementTree.fromstring(content)
        self.assertEquals(e.tag, 'html')
        
        body = e.find('body')
        self.assertNotEquals(body, None)
        
        img = body.find('img')
        self.assertNotEquals(img, None)
        
        src = img.get('src', default=None)
        self.assertNotEquals(src, None)
        
        url = urlex.hashedurl_pixelpng(uuid)
        #urltail = urlreverse( 'targetview-pixelpng', 
        #                      urlconf='linkanalytics.targeturls')
        #urltail = urltail[1:] # remove leading '/'
        #url = urlreverse( 'linkanalytics-accessview', 
        #                  kwargs={'uuid': uuid, 'tailpath':urltail})
        
        self.assertEquals(src, '{0}{1}'.format(app_settings.URLBASE, url))
        
    # check that DraftEmails cannot be sent more than once
    # check that the same email cannot be sent to the same recipient more than 
    #   once
    # check that emails actually get sent
    # check that each recipient has a different uuid
    # check that EmailRecipients contains the new recipients of the email
        
        
            
#==============================================================================#
    
