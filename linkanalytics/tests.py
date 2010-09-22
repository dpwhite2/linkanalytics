
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as urlreverse
from django.db import IntegrityError
from django.template import Template, Context

from models import TrackedUrl,TrackedUrlInstance,Trackee,Email,DraftEmail, TrackedUrlAccess
#from models import TRACKED_URL_TYPEABBREVS

import datetime
import unittest
import textwrap

from linkanalytics.util.htmltotext import HTMLtoText

import django
print '----------\n{0}\n----------'.format(str(django))


#==============================================================================#
# Test cases are automatically added to the test suite if they derive from 
# LinkAnalytics_TestCaseBase and their name ends with _TestCase.

#==============================================================================#
class UserLogin_Context(object):
    def __init__(self, client, username, password):
        self.client = client
        self.username = username
        self.password = password
    def __enter__(self):
        self.client.login(username=self.username, password=self.password)
    def __exit__(self, type, value, traceback):
        self.client.logout()

#==============================================================================#
class LinkAnalytics_TestCaseBase(TestCase):
    pass
    
class LinkAnalytics_DBTestCaseBase(LinkAnalytics_TestCaseBase):
    urls = 'linkanalytics.tests_urls'
    
    # sets site.domain to 'testserver' which is what Django calls the testserver within URLs
    fixtures = ['sites.json']
    
    def scoped_login(self, username, password):
        return UserLogin_Context(self.client, username, password)
    def setUp(self):
        self.today = datetime.date.today()
        self.users = []
    def create_users(self, n):
        for user in self.users:
            user.delete()
        self.users = [
                User.objects.create_user(username="user%d"%i,email="",password="password") 
                for i in range(2)
            ]
    def tearDown(self):
        TrackedUrl.objects.all().delete()
        TrackedUrlInstance.objects.all().delete()
        #TrackedUrlTarget.objects.all().delete()
        Trackee.objects.all().delete()
        Email.objects.all().delete()
        DraftEmail.objects.all().delete()
        
        for user in self.users:
            user.delete()
            
    def new_trackedurl(self, name):
        """Creates and saves a TrackedUrl"""
        u = TrackedUrl(name=name)
        u.save()
        return u
    def new_trackee(self, username):
        """Creates and saves a Trackee"""
        t = Trackee(username=username)
        t.save()
        return t
    
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
        
        self.assertEquals(i1.recent_access, otherday)
        self.assertEquals(i1.first_access, otherday)
        self.assertEquals(i1.access_count, 1)
        self.assertEquals(i1.was_accessed(), True)
        
        # A second access
        i1.on_access(success=True, url='')
        
        # .first_access should reflect previous access, but recent_access 
        # should reflect the most recent access.
        self.assertEquals(i1.recent_access.date(), datetime.date.today())
        self.assertEquals(i1.first_access, otherday)
        self.assertEquals(i1.access_count, 2)
        self.assertEquals(i1.was_accessed(), True)
        
        
        
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
        
        
        
class Email_TestCase(LinkAnalytics_DBTestCaseBase):
    pass
        
#==============================================================================#
# View tests:

class AccessTrackedUrl_TestCase(LinkAnalytics_DBTestCaseBase):
    pass

class CreateTrackedUrl_TestCase(LinkAnalytics_DBTestCaseBase):
    pass

class CreateTrackee_TestCase(LinkAnalytics_DBTestCaseBase):
    pass

#class CreateTrackedUrlTarget_TestCase(LinkAnalytics_DBTestCaseBase):
#    pass

#==============================================================================#
# Target View tests:

class ViewRedirect_TestCase(LinkAnalytics_DBTestCaseBase):
    def test_local_redirect(self):
        u = self.new_trackedurl('url1')
        t = self.new_trackee('trackee1')
        i = u.add_trackee(t)
        
        # The url we are resolving, using the default urls.py and targeturls.py:
        #   URLINSTANCE  TARGETVIEW
        #   URLINSTANCE = /linkanalytics/access/{uuid}
        #   TARGETVIEW =  /r/linkanalytics/testurl/
        urltail = urlreverse('redirect-local', urlconf='linkanalytics.targeturls', kwargs={'filepath':'linkanalytics/testurl/'})
        urltail = urltail[1:] # remove leading '/'
        url = urlreverse('linkanalytics-accessview', kwargs={'uuid': i.uuid, 'tailpath':urltail})
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
        urltail = urlreverse('redirect-http', urlconf='linkanalytics.targeturls', kwargs={'domain':'www.google.com','filepath':''})
        urltail = urltail[1:] # remove leading '/'
        url = urlreverse('linkanalytics-accessview', kwargs={'uuid': i.uuid, 'tailpath':urltail})
        
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


class ViewHtml_TestCase(LinkAnalytics_DBTestCaseBase):
    pass

class ViewPixelGif_TestCase(LinkAnalytics_DBTestCaseBase):
    pass

class ViewPixelPng_TestCase(LinkAnalytics_DBTestCaseBase):
    pass



#==============================================================================#
# Misc. tests:
        
class Access_TestCase(LinkAnalytics_DBTestCaseBase):
    pass
    
class Track_TemplateTag_TestCase(LinkAnalytics_TestCaseBase):
    def test_trail(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'trail' 'path/to/file.ext' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        self.assertEquals(s, '\n{% trackedurl linkid "path/to/file.ext" %}\n')
        
    def test_url(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'url' 'http://www.domain.org/path/to/file.html' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        self.assertEquals(s, '\n{% trackedurl linkid "http/www.domain.org/path/to/file.html" %}\n')
        
    def test_pixel(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'pixel' 'gif' %}
            {% track 'pixel' 'png' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        self.assertEquals(s, '\n{% trackedurl linkid "gpx" %}\n{% trackedurl linkid "ppx" %}\n')
        
        
    
class HTMLtoText_TestCase(LinkAnalytics_TestCaseBase):
    htmloutline = "<html><head></head><body>{0}</body></html>"
    
    def test_basic(self):
        html = self.htmloutline.format("This is some text.")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "This is some text.")
        
    def test_simple_paragraph(self):
        html = self.htmloutline.format("<p>A paragraph.</p>")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n")
        
    def test_two_paragraphs(self):
        html = self.htmloutline.format("<p>A paragraph.</p><p>Another paragraph.</p>")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n\nAnother paragraph.\n")
        
    def test_linebreak(self):
        html = self.htmloutline.format("One line.<br/>Two lines.")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "One line.\nTwo lines.")
    

def suite():
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name,val in globals().iteritems():
        if name.endswith('_TestCase') and issubclass(val, LinkAnalytics_TestCaseBase):
            test_suite.addTest(loader.loadTestsFromTestCase(val))
    return test_suite






