
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as urlreverse
from django.db import IntegrityError

from models import TrackedUrl,TrackedUrlInstance,Trackee,Email # TrackedUrlTarget
#from models import TRACKED_URL_TYPEABBREVS

import datetime
import unittest


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
        
        for user in self.users:
            user.delete()
    
#==============================================================================#
# Model tests:

#class TrackedUrlStats_TestCase(LinkAnalytics_TestCaseBase):
#    def test_unique_together(self):
#        pass
        
        
#class UrlTargetPair_TestCase(LinkAnalytics_TestCaseBase):
#    def test_unique_together(self):
#        u1 = TrackedUrl(name='Name1')
#        u1.save()
#        g = TrackedUrlTarget(name='target', view='H')
#        g.save()
#        
#        p = u1.add_target(g)
#        self.assertRaises(IntegrityError, u1.add_target, g)
        
        
class TrackedUrlInstance_TestCase(LinkAnalytics_TestCaseBase):
    def test_unique_together(self):
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        # Should not be able to save another item with same TrackedUrl and Trackee.
        self.assertRaises(IntegrityError, u1.add_trackee, t1)  # t1 is passed to add_trackee
        
    def test_basic(self):
        u = TrackedUrl(name='Name')
        u.save()
        t = Trackee(username='trackee0')
        t.save()
        
        i = u.add_trackee(t) # create a TrackedUrlInstance
        
        self.assertEquals(u.url_instances().count(), 1)
        self.assertEquals(u.url_instances()[0], i)
        self.assertEquals(t.url_instances().count(), 1)
        self.assertEquals(t.url_instances()[0], i)
        
    #def test_targets(self):
    #    #g = TrackedUrlTarget(name='target', view='H')
    #    #g.save()
    #    
    #    u = TrackedUrl(name='Name')
    #    u.save()
    #    u.add_target(g)
    #    t = Trackee(username='trackee0')
    #    t.save()        
    #    i = u.add_trackee(t)
    #    
    #    self.assertEquals(i.targets().count(), 1)
    #    self.assertEquals(i.targets()[0], g)
        
        
        
class Trackee_TestCase(LinkAnalytics_TestCaseBase):
    def test_unique_username(self):
        t1 = Trackee(username='trackee1')
        t1.save()
        t2 = Trackee(username='trackee1')
        # should not allow saving object with same name
        self.assertRaises(IntegrityError, t2.save)
        
    def test_urls(self):
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
        
        
#class TrackedUrlTarget_TestCase(LinkAnalytics_TestCaseBase):
#    def test_unique_name(self):
#        g1 = TrackedUrlTarget(name='target1', view='H')
#        g1.save()
#        g2 = TrackedUrlTarget(name='target1', view='H')
#        # should not allow saving object with same name
#        self.assertRaises(IntegrityError, g2.save)
        
        
class TrackedUrl_TestCase(LinkAnalytics_TestCaseBase):
    def test_trackees(self):
        u1 = TrackedUrl(name='Name1')
        u1.save()
        u2 = TrackedUrl(name='Name2')
        u2.save()
        
        t1 = Trackee(username='trackee1')
        t1.save()
        t2 = Trackee(username='trackee2')
        t2.save()
        
        i1 = u1.add_trackee(t1)
        i2 = u2.add_trackee(t1)
        
        self.assertEquals(u1.trackees.count(), 1)
        self.assertEquals(u1.trackees.all()[0], t1)
        self.assertEquals(u2.trackees.count(), 1)
        self.assertEquals(u2.trackees.all()[0], t1)
        
    def test_urlInstances(self):
        # TrackedUrl.url_instances() and TrackedUrl.url_instances_read()
        u1 = TrackedUrl(name='Name1')
        u1.save()
        
        # empty url_instances
        self.assertEquals(u1.url_instances().count(),0)
        self.assertEquals(u1.url_instances_read().count(),0)
        
        t1 = Trackee(username='trackee1')
        t1.save()
        i1 = u1.add_trackee(t1)
        
        # non-empty url_instances
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),0)
        
        u2 = TrackedUrl(name='Name2')
        u2.save()
        
        i2 = u2.add_trackee(t1)
        
        # more than one TrackedUrl object
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),0)
        
        ##targetname1 = 'target1'
        #g1 = TrackedUrlTarget(name=targetname1, view='H')
        #g1.save()
        #u1.add_target(g1)
        
        i1.on_access()
        
        # with single access
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),1)
        
        #targetname2 = 'target2'
        #g2 = TrackedUrlTarget(name=targetname2, view='H')
        #g2.save()
        #u1.add_target(g2)
        
        i1.on_access()
        
        # with a second access
        self.assertEquals(u1.url_instances().count(),1)
        self.assertEquals(u1.url_instances_read().count(),1)
        
        
        
class Email_TestCase(LinkAnalytics_TestCaseBase):
    pass
        
#==============================================================================#
# View tests:

class AccessTrackedUrl_TestCase(LinkAnalytics_TestCaseBase):
    pass

class CreateTrackedUrl_TestCase(LinkAnalytics_TestCaseBase):
    pass

class CreateTrackee_TestCase(LinkAnalytics_TestCaseBase):
    pass

#class CreateTrackedUrlTarget_TestCase(LinkAnalytics_TestCaseBase):
#    pass

#==============================================================================#
# Target View tests:

class ViewUnknown_TestCase(LinkAnalytics_TestCaseBase):
    pass

class ViewHtml_TestCase(LinkAnalytics_TestCaseBase):
    pass

class ViewTxt_TestCase(LinkAnalytics_TestCaseBase):
    pass

class ViewGif_TestCase(LinkAnalytics_TestCaseBase):
    pass



#==============================================================================#
# Misc. tests:
        
class Access_TestCase(LinkAnalytics_TestCaseBase):
    def test_initialAccessValues(self):
        # instance that has not been accessed yet
        u1 = TrackedUrl(name='Name1')
        u1.save()        
        t1 = Trackee(username='trackee1')
        t1.save()        
        i1 = u1.add_trackee(t1)
        
        self.assertEquals(i1.was_accessed(), False)
        self.assertEquals(i1.access_count, 0)
        self.assertEquals(i1.recent_access, None)
        self.assertEquals(i1.first_access, None)
        
        #self.assertEquals(i1.trackedurlstats_set.all().count(), 0)
        
    def test_unknownTarget_basic(self):
        # instance that was accessed via an unknown targetname
        u1 = TrackedUrl(name='Name1')
        u1.save()
        
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        
        #targetname = "A target name that doesn't exist in the database"
        i1.on_access()
        
        self.assertEquals(i1.was_accessed(), True)
        self.assertEquals(i1.access_count, 1)
        self.assertEquals(i1.recent_access, datetime.date.today())
        self.assertEquals(i1.first_access, datetime.date.today())
        
        #self.assertEquals(i1.trackedurlstats_set.all().count(), 1)
        #self.assertEquals(i1.trackedurlstats_set.all()[0].instance, i1)
        
    def test_knownTarget_basic(self):
        # instance accessed via a known targetname
        #targetname = 'target'
        #g1 = TrackedUrlTarget(name=targetname, view='H')
        #g1.save()
        
        u1 = TrackedUrl(name='Name1')
        u1.save()
        
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        #u1.add_target(g1)
        
        i1.on_access()
        
        self.assertEquals(i1.was_accessed(), True)
        self.assertEquals(i1.access_count, 1)
        self.assertEquals(i1.recent_access, datetime.date.today())
        self.assertEquals(i1.first_access, datetime.date.today())
        
        #self.assertEquals(i1.trackedurlstats_set.all().count(), 1)
        #self.assertEquals(i1.trackedurlstats_set.all()[0].instance, i1)
    

def suite():
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    #test_suite.addTest(loader.loadTestsFromTestCase(Model_TestCase))
    #test_suite.addTest(loader.loadTestsFromTestCase(Access_TestCase))
    for name,val in globals().iteritems():
        if name.endswith('_TestCase') and issubclass(val, LinkAnalytics_TestCaseBase):
            test_suite.addTest(loader.loadTestsFromTestCase(val))
    return test_suite






