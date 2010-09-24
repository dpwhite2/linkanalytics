import datetime
import unittest
import textwrap
import re

from django.test import TestCase
from django.core import mail as django_email
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as urlreverse
from django.db import IntegrityError
from django.template import Template, Context

from linkanalytics.models import TrackedUrl,TrackedUrlInstance,Trackee,Email,DraftEmail,TrackedUrlAccess


from linkanalytics.util.htmltotext import HTMLtoText
from linkanalytics import email as LAemail

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
        
    # check that DraftEmails cannot be sent more than once
    # check that the same email cannot be sent to the same recipient more than once
    # check that emails actually get sent
    # check that each recipient has a different uuid
    # check that EmailRecipients contains the new recipients of the email
        
        
    
        
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
    

    
class HtmlDocument_TestCase(LinkAnalytics_TestCaseBase):
    def test_basic(self):
        html = "<html><head></head><body></body></html>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_title(self):
        html = "<html><head><title>A Title</title></head><body></body></html>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '<title>A Title</title>')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_bodycontent(self):
        html = "<html><head></head><body><h1>A heading.</h1><p>A paragraph.</p></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '<h1>A heading.</h1><p>A paragraph.</p>')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_pi(self):
        html = "<?xml version='1.0'?><html><head></head><body></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, "<?xml version='1.0'?>")
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
class CompileEmail_TestCase(LinkAnalytics_TestCaseBase):
    def test_basic(self):
        htmlsrc = "<html><head></head><body></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_headcontent(self):
        htmlsrc = "<html><head><title>A Title</title></head><body></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_bodycontent(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '\nA paragraph.\n')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_trackTrail(self):
        htmlsrc = "<html><head></head><body>{% track 'trail' 'path/file.ext' %}</body></html>"
        tag = '{% trackedurl linkid "path/file.ext" %}'
        htmlres = """<html><head></head><body>{0}</body></html>""".format(tag)
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, tag)
        self.assertEqualsHtml(html, htmlres)
        
    def test_header_footer(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        header = '<h1>A Header</h1>'
        footer = '<div>A footer.</div>'
        htmlres = "<html><head></head><body>{0}<p>A paragraph.</p>{1}</body></html>".format(header,footer)
        textres = "\n{0}\n\nA paragraph.\n{1}".format("A Header","A footer.")
        text,html = LAemail.compile_email(htmlsrc, html_header=header, html_footer=footer)
        self.assertEquals(text, textres)
        self.assertEqualsHtml(html, htmlres)
        
        
class InstantiateEmails_TestCase(LinkAnalytics_TestCaseBase):
    def test_basic(self):
        htmlsrc = "<html><head></head><body></body></html>"
        textsrc = ""
        urlbase = 'http://example.com'
        uuid = '0'*32
        it = LAemail.instantiate_emails(textsrc,htmlsrc,urlbase,(uuid,))
        text,html = it.next()
        self.assertEquals(text, textsrc)
        self.assertEquals(html, htmlsrc)
        
    def test_trail(self):
        htmlsrc = "<html><head></head><body>{% trackedurl linkid 'path/to/file.ext' %}</body></html>"
        textsrc = "{% trackedurl linkid 'path/to/file.ext' %}"
        urlbase = 'http://example.com'
        uuid = '0'*32
        it = LAemail.instantiate_emails(textsrc,htmlsrc,urlbase,(uuid,))
        text,html = it.next()
        url = 'http://example.com/{0}/path/to/file.ext'.format(uuid)
        self.assertEquals(text, '{0}'.format(url))
        self.assertEquals(html, "<html><head></head><body>{0}</body></html>".format(url))

    
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
            {% trackedurl linkid "path/to/file.ext" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        c = Context({'linkid':uuid, 'urlbase':'http://example.com'})
        s = t.render(c)
        self.assertEquals(s, '\nhttp://example.com/{0}/path/to/file.ext\n'.format(uuid))
        
    def test_url(self):
        templtxt = """\
            {% load tracked_links %}
            {% trackedurl linkid "http/www.example.com/path/file.html" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        c = Context({'linkid':uuid, 'urlbase':'http://example.com'})
        s = t.render(c)
        self.assertEquals(s, '\nhttp://example.com/{0}/http/www.example.com/path/file.html\n'.format(uuid))
        
    
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






