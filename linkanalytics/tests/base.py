import re
import unittest
import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, Trackee
from linkanalytics.models import TrackedUrlAccess
from linkanalytics.email.models import Email, DraftEmail, EmailRecipients

# Disable Nose test autodiscovery for this module.
__test__ = False

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
    urls = 'linkanalytics.tests.test_urls'
    
    def assertEqualsHtml(self, a, b):
        """Check whether two objects, a and b, are equal when basic HTML rules 
           are taken into account.  This includes regarding all whitespace as 
           identical.  The objects must be strings.
        """
        aa = _re_adjacenttags.sub(r'\1', a).strip()
        bb = _re_adjacenttags.sub(r'\1 ', b).strip()
        aa = _re_whitespace.sub(' ', aa)
        bb = _re_whitespace.sub(' ', bb)
        msg = '"{0}" != "{1}"'.format(a, b)
        msg += '\n\nmodified strings:\n"{0}" != "{1}"'.format(aa, bb)
        self.assertTrue(aa==bb, msg)
    
class LinkAnalytics_DBTestCaseBase(LinkAnalytics_TestCaseBase):
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
                User.objects.create_user(username="user%d"%i,
                                         email="user%d@example.com"%i,
                                         password="password") 
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
        EmailRecipients.objects.all().delete()
        
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
# Use the following function to generate a TestSuite for a given module.  
# Modules do not have to do this themselves--the package handles this.
def autogenerate_testsuite(globals):
    """globals is a dict of global names.  Test modules should use globals() 
       for this argument.
    """
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name, val in globals.iteritems():
        if name.endswith('_TestCase') and \
           issubclass(val, LinkAnalytics_TestCaseBase):
            test_suite.addTest(loader.loadTestsFromTestCase(val))
    return test_suite
    
