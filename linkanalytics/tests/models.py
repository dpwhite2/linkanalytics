import datetime
import xml.etree.ElementTree

from django.db import IntegrityError
from django.core import mail as django_email
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.tests import LinkAnalytics_TestCaseBase, LinkAnalytics_DBTestCaseBase
from linkanalytics.tests import urlreverse_redirect_http
from linkanalytics.tests import urlreverse_redirect_local

from linkanalytics.models import TrackedUrl,TrackedUrlInstance,Trackee,Email,DraftEmail,TrackedUrlAccess
from linkanalytics import app_settings

#==============================================================================#
# Model tests:
        
class TrackedUrlInstance_TestCase(LinkAnalytics_DBTestCaseBase):
    def test_unique_together(self):
        # Check that the same Trackee can not be added to a TrackedUrl more than once.
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        # Should not be able to save another item with same TrackedUrl and Trackee.
        self.assertRaises(IntegrityError, u1.add_trackee, t1)  # t1 is passed to add_trackee
        
    def test_basic(self):
        # Check the attributes on a TrackedUrlInstance that has not been accessed.
        u = TrackedUrl(name='Name')
        u.save()
        t = Trackee(username='trackee0')
        t.save()
        
        i = u.add_trackee(t) # create a TrackedUrlInstance
        
        self.assertEquals(i.first_access, None)
        self.assertEquals(i.recent_access, None)
        self.assertEquals(i.access_count, 0)
        self.assertEquals(i.was_accessed(), False)
        
    def test_cancelled_access(self):
        # Cancel an access using the Accessed object returned by on_access()
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        
        i1.on_access(success=False, url='')
        
        self.assertEquals(i1.first_access, None)
        self.assertEquals(i1.recent_access, None)
        self.assertEquals(i1.access_count, 0)
        self.assertEquals(i1.was_accessed(), False)
        
        
    def test_single_access(self):
        # Check the attributes on a TrackedUrlInstance that has been accessed once.
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        
        i1.on_access(success=True, url='')
        
        self.assertEquals(i1.recent_access.date(), datetime.date.today())
        self.assertEquals(i1.first_access.date(), datetime.date.today())
        self.assertEquals(i1.access_count, 1)
        self.assertEquals(i1.was_accessed(), True)
        
    def test_second_access(self):
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        
        # Simulate an access on a previous day.
        otherday = datetime.datetime.today() - datetime.timedelta(days=7)
        a1 = TrackedUrlAccess(instance=i1, time=otherday, count=1, url='')
        a1.save()
        
        self.assertEquals(i1.recent_access.date(), otherday.date())
        self.assertEquals(i1.first_access.date(), otherday.date())
        self.assertEquals(i1.access_count, 1)
        self.assertEquals(i1.was_accessed(), True)
        
        # A second access
        i1.on_access(success=True, url='')
        
        # .first_access should reflect previous access, but recent_access 
        # should reflect the most recent access.
        self.assertEquals(i1.recent_access.date(), datetime.date.today())
        self.assertEquals(i1.first_access.date(), otherday.date())
        self.assertEquals(i1.access_count, 2)
        self.assertEquals(i1.was_accessed(), True)
        
        
#==============================================================================#
        
class Trackee_TestCase(LinkAnalytics_DBTestCaseBase):
    def test_unique_username(self):
        # Check that Trackees cannot have duplicate names.
        t1 = Trackee(username='trackee1')
        t1.save()
        t2 = Trackee(username='trackee1')
        # should not allow saving object with same name
        self.assertRaises(IntegrityError, t2.save)
        
    def test_urls(self):
        # Check the Trackee.urls() method
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        t2 = Trackee(username='trackee2')
        t2.save()
        i1 = u1.add_trackee(t1)
        i2 = u1.add_trackee(t2)
        
        self.assertEquals(t1.urls().count(), 1)
        self.assertEquals(t1.urls()[0], u1)
        self.assertEquals(t2.urls().count(), 1)
        self.assertEquals(t2.urls()[0], u1)
        
        
#==============================================================================#

class TrackedUrl_TestCase(LinkAnalytics_DBTestCaseBase):
    def test_trackees(self):
        # Check the TrackedUrl.trackees attribute
        u1 = TrackedUrl(name='Name1')
        u1.save()
        
        self.assertEquals(u1.trackees.exists(), False)
        
        t1 = Trackee(username='trackee1')
        t1.save()
        
        # Merely create a Trackee should not associate it with a TrackedUrl
        self.assertEquals(u1.trackees.exists(), False)
        
        i1 = u1.add_trackee(t1)
        
        # ...But once added, the Trackee should be found in the trackees attribute.
        self.assertEquals(u1.trackees.exists(), True)
        self.assertEquals(u1.trackees.count(), 1)
        self.assertEquals(u1.trackees.all()[0], t1)
        
        u2 = TrackedUrl(name='Name2')
        u2.save()
        t2 = Trackee(username='trackee2')
        t2.save()
        i2 = u2.add_trackee(t1)
        
        # TrackeUrls and Trackees should not affect other TrackedUrls
        self.assertEquals(u1.trackees.count(), 1)
        self.assertEquals(u1.trackees.all()[0], t1)
        self.assertEquals(u2.trackees.count(), 1)
        self.assertEquals(u2.trackees.all()[0], t1)
        
        i2b = u1.add_trackee(t2)
        
        # Check that a second Trackee was added (assumes Trackees in 
        # trackees.all() appear in the same order in which they were added.)
        self.assertEquals(u1.trackees.count(), 2)
        self.assertEquals(u1.trackees.all()[0], t1)
        self.assertEquals(u1.trackees.all()[1], t2)
        
        
        
    def test_urlInstances(self):
        # Check the methods: TrackedUrl.url_instances() and TrackedUrl.url_instances_read()
        u1 = TrackedUrl(name='Name1')
        u1.save()
        
        # Both methods should be empty at first.
        self.assertEquals(u1.url_instances().count(),0)
        self.assertEquals(u1.url_instances_read().count(),0)
        
        t1 = Trackee(username='trackee1')
        t1.save()
        i1 = u1.add_trackee(t1)
        
        # Adding a Trackee should be reflected in url_instances(), but not url_instances_read()
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),0)
        
        u2 = TrackedUrl(name='Name2')
        u2.save()
        
        i2 = u2.add_trackee(t1)
        
        # A Trackee may be associated with more than one TrackedUrl, but any 
        # such TrackedUrls should have separate url_instances.
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),0)
        self.assertEquals(u2.url_instances().count(),1)
        self.assertEquals(u2.url_instances_read().count(),0)
        self.assertNotEquals(u1.url_instances()[0], u2.url_instances()[0])
        # The separate TrackedUrlInstances refer to the same Trackee.
        self.assertEquals(u1.url_instances()[0].trackee, u2.url_instances()[0].trackee)
        
        i1.on_access(success=True, url='')
        
        # Once accessed, url_instances() remains the same but 
        # url_instances_read() should indicate that the instance has now been 
        # read.
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),1)
        
        i1.on_access(success=True, url='')
        
        # A second access should not affect the object counts.
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),1)
        
        
#==============================================================================#

class Email_TestCase(LinkAnalytics_DBTestCaseBase):
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
        self.assertEquals(django_email.outbox[0].recipients(), ['user@example.com'])
        
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
        
        urltail = urlreverse('targetview-pixelpng', urlconf='linkanalytics.targeturls')
        urltail = urltail[1:] # remove leading '/'
        url = urlreverse('linkanalytics-accessview', kwargs={'uuid': uuid, 'tailpath':urltail})
        
        self.assertEquals(src, '{0}{1}'.format(app_settings.URLBASE, url))
        
    # check that DraftEmails cannot be sent more than once
    # check that the same email cannot be sent to the same recipient more than once
    # check that emails actually get sent
    # check that each recipient has a different uuid
    # check that EmailRecipients contains the new recipients of the email
        
        
#==============================================================================#
    
