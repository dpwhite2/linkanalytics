
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as urlreverse
from django.db import IntegrityError

from models import TrackedUrl,TrackedUrlInstance,TrackedUrlTarget,Trackee,Email
from models import TRACKED_URL_TYPES

import datetime
import unittest



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
        TrackedUrlTarget.objects.all().delete()
        Trackee.objects.all().delete()
        Email.objects.all().delete()
        
        for user in self.users:
            user.delete()
    
#
class Model_TestCase(LinkAnalytics_TestCaseBase):
    def test_UrlInstance_basic(self):
        u = TrackedUrl(name='Name')
        u.save()
        t = Trackee(username='trackee0')
        t.save()
        
        i = u.add_trackee(t)
        
        self.assertEquals(u.url_instances().count(), 1)
        self.assertEquals(u.url_instances()[0], i)
        
        self.assertEquals(t.url_instances().count(), 1)
        self.assertEquals(t.url_instances()[0], i)
        
    def test_UrlTarget_basic(self):
        g = TrackedUrlTarget(name='target', urltype='H', path='')
        g.save()
        
        u = TrackedUrl(name='Name')
        u.save()
        u.add_target(g)
        t = Trackee(username='trackee0')
        t.save()
        
        self.assertEquals(TrackedUrlTarget.objects.all().count(), 1)
        
        self.assertEquals(u.targets.count(), 1)
        self.assertEquals(u.targets.all()[0], g)
        
    def test_UrlInstance_targets(self):
        g = TrackedUrlTarget(name='target', urltype='H', path='')
        g.save()
        
        u = TrackedUrl(name='Name')
        u.save()
        u.add_target(g)
        t = Trackee(username='trackee0')
        t.save()        
        i = u.add_trackee(t)
        
        self.assertEquals(i.targets().count(), 1)
        self.assertEquals(i.targets()[0], g)
        
    def test_UrlInstance_duplicateError(self):
        u1 = TrackedUrl(name='Name1')
        u1.save()
        t1 = Trackee(username='trackee1')
        t1.save()
        
        i1 = u1.add_trackee(t1)
        # Should not be able to save another item with same TrackedUrl and Trackee.
        self.assertRaises(IntegrityError, u1.add_trackee, t1)  # t1 is passed to add_trackee
        
    def test_Trackee_urls(self):
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
        
    def test_TrackedUrl_trackees(self):
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
    

def suite():
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(Model_TestCase))
    return test_suite






