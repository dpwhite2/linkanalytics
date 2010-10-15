import datetime

from django.db import IntegrityError

from linkanalytics.models import Tracker, TrackedInstance, Visitor, Access
from linkanalytics.models import _ACCESS_SUCCESS, _ACCESS_FAILURE_UUID
from linkanalytics.models import _ACCESS_FAILURE_HASH, _ACCESS_ERROR_TARGETVIEW
from linkanalytics import urlex

import base

#==============================================================================#
# Model tests:
        
class TrackedInstance_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_unique_together(self):
        # Check that the same Visitor can not be added to a Tracker more 
        # than once.
        t = self.new_tracker('tracker')
        v = self.new_visitor('visitor')
        
        t.add_visitor(v)
        # Should not be able to save item with same Tracker and Visitor.
        self.assertRaises(IntegrityError, t.add_visitor, v)  # v is passed
                                                               # to add_visitor
        
    def test_basic(self):
        # Check the attributes on a TrackedInstance that has not been 
        # accessed.
        t = self.new_tracker('tracker')
        v = self.new_visitor('visitor')
        
        i = t.add_visitor(v) # create a TrackedInstance
        
        self.assertEquals(i.first_access, None)
        self.assertEquals(i.recent_access, None)
        self.assertEquals(i.access_count, 0)
        self.assertEquals(i.was_accessed(), False)
        
    def test_cancelled_access(self):
        # Cancel an access using the Accessed object returned by on_access()
        t = self.new_tracker('tracker')
        v = self.new_visitor('visitor')
        
        i = t.add_visitor(v)
        
        i.on_access(result=_ACCESS_ERROR_TARGETVIEW, url='')
        
        self.assertEquals(i.first_access, None)
        self.assertEquals(i.recent_access, None)
        self.assertEquals(i.access_count, 0)
        self.assertEquals(i.was_accessed(), False)
        
        
    def test_single_access(self):
        # Check the attributes on a TrackedInstance that has been accessed 
        # once.
        t = self.new_tracker('tracker')
        v = self.new_visitor('visitor')
        
        i = t.add_visitor(v)
        
        i.on_access(result=_ACCESS_SUCCESS, url='')
        
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.first_access.date(),  datetime.date.today())
        self.assertEquals(i.access_count, 1)
        self.assertEquals(i.was_accessed(), True)
        
    def test_second_access(self):
        t = self.new_tracker('tracker')
        v = self.new_visitor('visitor')
        
        i = t.add_visitor(v)
        
        # Simulate an access on a previous day.
        otherday = datetime.datetime.today() - datetime.timedelta(days=7)
        a1 = Access(instance=i, time=otherday, count=1, url='', 
                    result=_ACCESS_SUCCESS)
        a1.save()
        
        self.assertEquals(i.recent_access.date(), otherday.date())
        self.assertEquals(i.first_access.date(), otherday.date())
        self.assertEquals(i.access_count, 1)
        self.assertEquals(i.was_accessed(), True)
        
        # A second access
        i.on_access(result=_ACCESS_SUCCESS, url='')
        
        # .first_access should reflect previous access, but recent_access 
        # should reflect the most recent access.
        self.assertEquals(i.recent_access.date(), datetime.date.today())
        self.assertEquals(i.first_access.date(), otherday.date())
        self.assertEquals(i.access_count, 2)
        self.assertEquals(i.was_accessed(), True)
        
       
        
        
        
#==============================================================================#
        
class Visitor_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_unique_username(self):
        # Check that Visitors cannot have duplicate names.
        v1 = Visitor(username='visitor1')
        v1.save()
        v2 = Visitor(username='visitor1')
        # should not allow saving object with same name
        self.assertRaises(IntegrityError, v2.save)
        
    def test_urls(self):
        # Check the Visitor.urls() method
        t = self.new_tracker('tracker')
        v1 = self.new_visitor('visitor1')
        v2 = self.new_visitor('visitor2')
        t.add_visitor(v1)
        t.add_visitor(v2)
        
        self.assertEquals(v1.urls().count(), 1)
        self.assertEquals(v1.urls()[0], t)
        self.assertEquals(v2.urls().count(), 1)
        self.assertEquals(v2.urls()[0], t)
        
        
#==============================================================================#

class Tracker_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_visitors(self):
        # Check the Tracker.visitors attribute
        t1 = self.new_tracker('tracker1')
        
        self.assertEquals(t1.visitors.exists(), False)
        
        v1 = self.new_visitor('visitor1')
        
        # Merely create a Visitor should not associate it with a Tracker
        self.assertEquals(t1.visitors.exists(), False)
        
        t1.add_visitor(v1)
        
        # ...But once added, the Visitor should be found in the visitors 
        # attribute.
        self.assertEquals(t1.visitors.exists(), True)
        self.assertEquals(t1.visitors.count(), 1)
        self.assertEquals(t1.visitors.all()[0], v1)
        
        t2 = self.new_tracker('tracker2')
        v2 = self.new_visitor('visitor2')
        t2.add_visitor(v1)
        
        # TrackeUrls and Visitors should not affect other Trackers
        self.assertEquals(t1.visitors.count(), 1)
        self.assertEquals(t1.visitors.all()[0], v1)
        self.assertEquals(t2.visitors.count(), 1)
        self.assertEquals(t2.visitors.all()[0], v1)
        
        t1.add_visitor(v2)
        
        # Check that a second Visitor was added (assumes Visitors in 
        # visitors.all() appear in the same order in which they were added.)
        self.assertEquals(t1.visitors.count(), 2)
        self.assertEquals(t1.visitors.all()[0], v1)
        self.assertEquals(t1.visitors.all()[1], v2)
        
        
        
    def test_trackedInstances(self):
        # Check the methods: Tracker.url_instances() and 
        #                    Tracker.url_instances_read()
        t1 = self.new_tracker('tracker1')
        
        # Both methods should be empty at first.
        self.assertEquals(t1.instances().count(), 0)
        self.assertEquals(t1.instances_read().count(), 0)
        
        v1 = self.new_visitor('visitor1')
        i1 = t1.add_visitor(v1)
        
        # Adding a Visitor should be reflected in url_instances(), but not 
        # url_instances_read()
        self.assertEquals(t1.instances().count(), 1)
        self.assertEquals(t1.instances_read().count(), 0)
        
        t2 = self.new_tracker('tracker2')
        
        t2.add_visitor(v1)
        
        # A Visitor may be associated with more than one Tracker, but any 
        # such Trackers should have separate url_instances.
        self.assertEquals(t1.instances().count(), 1)
        self.assertEquals(t1.instances_read().count(), 0)
        self.assertEquals(t2.instances().count(), 1)
        self.assertEquals(t2.instances_read().count(), 0)
        self.assertNotEquals(t1.instances()[0], t2.instances()[0])
        # The separate TrackedInstances refer to the same Visitor.
        self.assertEquals(t1.instances()[0].visitor, 
                          t2.instances()[0].visitor)
        
        i1.on_access(result=_ACCESS_SUCCESS, url='')
        
        # Once accessed, instances() remains the same but 
        # instances_read() should indicate that the instance has now been 
        # read.
        self.assertEquals(t1.instances().count(), 1)
        self.assertEquals(t1.instances_read().count(), 1)
        
        i1.on_access(result=_ACCESS_SUCCESS, url='')
        
        # A second access should not affect the object counts.
        self.assertEquals(t1.instances().count(), 1)
        self.assertEquals(t1.instances_read().count(), 1)
        
        
#==============================================================================#
class GenerateHash_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        # A very simple test.  Only tests that the hash function exists and 
        # returns the same hash value when given the same input.
        
        from linkanalytics.models import _create_uuid
        i = _create_uuid()
        s = 'This is some data to be hashed.'
        
        a = urlex.generate_urlhash(i,s)
        b = urlex.generate_urlhash(i,s)
        
        self.assertEquals(a, b)
    
#==============================================================================#

