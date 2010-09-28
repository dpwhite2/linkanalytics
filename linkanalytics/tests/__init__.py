import datetime
import unittest
import textwrap
import re
import xml.etree.ElementTree

from django.test import TestCase
from django.core import mail as django_email
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as urlreverse
from django.db import IntegrityError
from django.template import Template, Context

from linkanalytics.models import TrackedUrl,TrackedUrlInstance,Trackee,Email,DraftEmail,TrackedUrlAccess


from linkanalytics.util.htmltotext import HTMLtoText
from linkanalytics import email as LAemail
from linkanalytics import app_settings



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
_re_whitespace = re.compile(r'\s+')
_HTMLTAG = r'''</?[A-Za-z0-9 ='"\\:.%+]+>'''  # includes the tag and attributes
_re_adjacenttags = re.compile(r'('+_HTMLTAG+r')\s+(?='+_HTMLTAG+r')')

class LinkAnalytics_TestCaseBase(TestCase):
    def assertEqualsHtml(self, a, b):
        """Check whether two objects, a and b, are equal when basic HTML rules 
           are taken into account.  This includes regarding all whitespace as 
           identical.  The objects must be strings.
        """
        aa = _re_adjacenttags.sub(r'\1', a).strip()
        bb = _re_adjacenttags.sub(r'\1 ', b).strip()
        aa = _re_whitespace.sub(' ', aa)
        bb = _re_whitespace.sub(' ', bb)
        msg = '"{0}" != "{1}"'.format(a,b)
        msg += '\n\nmodified strings:\n"{0}" != "{1}"'.format(aa,bb)
        self.assertTrue(aa==bb, msg)
    
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
                User.objects.create_user(username="user%d"%i,email="user%d@example.com"%i,password="password") 
                for i in range(n)
            ]
    def tearDown(self):
        TrackedUrl.objects.all().delete()
        TrackedUrlAccess.objects.all().delete()
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
# Utility function used by a many tests below
def _put_htmldoc_newlines(data):
    """Put newlines into html source where HtmlDocument places them."""
    data = data.replace('<html>','<html>\n')
    data = data.replace('</html>','</html>\n')
    data = data.replace('</head>','</head>\n')
    data = data.replace('</body>','</body>\n')
    return data
    
def urlreverse_redirect_http(uuid, domain, filepath=''):
    urltail = urlreverse('redirect-http', urlconf='linkanalytics.targeturls', kwargs={'domain':domain,'filepath':filepath})
    urltail = urltail[1:] # remove leading '/'
    return urlreverse('linkanalytics-accessview', kwargs={'uuid': uuid, 'tailpath':urltail})
    
def urlreverse_redirect_local(uuid, filepath):
    urltail = urlreverse('redirect-local', urlconf='linkanalytics.targeturls', kwargs={'filepath':filepath})
    urltail = urltail[1:] # remove leading '/'
    return urlreverse('linkanalytics-accessview', kwargs={'uuid': uuid, 'tailpath':urltail})
    
#==============================================================================#
# Model tests:

    
        
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
        ##urltail = urlreverse('redirect-local', urlconf='linkanalytics.targeturls', kwargs={'filepath':'linkanalytics/testurl/'})
        ##urltail = urltail[1:] # remove leading '/'
        ##url = urlreverse('linkanalytics-accessview', kwargs={'uuid': i.uuid, 'tailpath':urltail})
        url = urlreverse_redirect_local(i.uuid, filepath='linkanalytics/testurl/')
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
        url = urlreverse_redirect_http(uuid=i.uuid, domain='www.google.com')
        ##urltail = urlreverse('redirect-http', urlconf='linkanalytics.targeturls', kwargs={'domain':'www.google.com','filepath':''})
        ##urltail = urltail[1:] # remove leading '/'
        ##url = urlreverse('linkanalytics-accessview', kwargs={'uuid': i.uuid, 'tailpath':urltail})
        
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
        

class TrackedUrl_TemplateTag_TestCase(LinkAnalytics_TestCaseBase):
    def test_basic(self):
        templtxt = """\
            {% load tracked_links %}
            {% trackedurl linkid "r/path/to/file.ext" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        urlbase = 'http://example.com'
        c = Context({'linkid':uuid, 'urlbase':urlbase})
        s = t.render(c)
        url = urlreverse_redirect_local(uuid=uuid, filepath='path/to/file.ext')
        self.assertEquals(s, '\n{0}{1}\n'.format(urlbase,url))
        
    def test_url(self):
        templtxt = """\
            {% load tracked_links %}
            {% trackedurl linkid "http/www.example.com/path/file.html" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        urlbase = 'http://example.com'
        c = Context({'linkid':uuid, 'urlbase':urlbase})
        s = t.render(c)
        url = urlreverse_redirect_http(uuid=uuid, domain='www.example.com', filepath='path/file.html')
        self.assertEquals(s, '\n{0}{1}\n'.format(urlbase,url))
        
    
    
#==============================================================================#
# Import other tests so they are picked up by the suite() function below
from linkanalytics.tests.email import *
from linkanalytics.tests.models import *

def suite():
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name,val in globals().iteritems():
        if name.endswith('_TestCase') and issubclass(val, LinkAnalytics_TestCaseBase):
            test_suite.addTest(loader.loadTestsFromTestCase(val))
    return test_suite






