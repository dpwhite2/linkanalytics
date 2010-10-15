import re
import unittest
import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from linkanalytics.models import Tracker, TrackedInstance, Visitor
from linkanalytics.models import Access

# Disable Nose test autodiscovery for this module.
__test__ = False

#==============================================================================#
# Test cases are automatically added to the test suite if they derive from 
# LinkAnalytics_TestCaseBase and their name ends with _TestCase.

#==============================================================================#
class UserLogin_Context(object):
    """Class for use with Python's with statement to ease the writing of tests 
       that involve user logins.
    """
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
    """Base TestCase class for all Linkanalytics test cases."""
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
    """Base TestCase class for all Linkanalytics test cases which access the 
       database.  This automatically destroys all Model objects in tearDown() 
       among other things.
    """
    
    def scoped_login(self, username, password):
        """Allows the login functionality to be used via the with statement, to 
           make coding somewhat simpler.
        """
        return UserLogin_Context(self.client, username, password)
        
    def setUp(self):
        self.today = datetime.date.today()
        self.users = []
        
    def create_users(self, n):
        """Create n users for a test case.  The users will be named userN where 
           N is the index of the user.  Users can be accessed through the 
           member variable 'users' which is a list of Users.
        """
        for user in self.users:
            user.delete()
        self.users = [
                User.objects.create_user(username="user%d"%i,
                                         email="user%d@example.com"%i,
                                         password="password") 
                for i in range(n)
            ]
    def tearDown(self):
        Tracker.objects.all().delete()
        Access.objects.all().delete()
        TrackedInstance.objects.all().delete()
        Visitor.objects.all().delete()
        
        for user in self.users:
            user.delete()
            
    def new_tracker(self, name=None):
        """Creates and saves a Tracker"""
        if not name:
            name = 'tracker{0}'.format(Tracker.objects.count()+1)
        t = Tracker(name=name)
        t.save()
        return t
        
    def new_visitor(self, username=None):
        """Creates and saves a Visitor"""
        if not username:
            username = 'visitor{0}'.format(Visitor.objects.count()+1)
        v = Visitor(username=username)
        v.save()
        return v
        
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
    
