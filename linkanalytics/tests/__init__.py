import unittest

from linkanalytics.tests import base
from linkanalytics.tests import helpers

#==============================================================================#
# Test modules...
from linkanalytics.tests import views, templatetags, models, util, email

# List of all test modules containing tests.  
_testmodules = [views,templatetags,models,util,email]

# Import all test cases so they appear in this module.  This appears to be 
# needed for Hudson automated testing.
for m in _testmodules:
    for name,val in m.__dict__.iteritems():
        if name.endswith('_TestCase') and issubclass(val, base.LinkAnalytics_TestCaseBase):
            globals()[name] = val

#==============================================================================#

def suite():
    test_suite = unittest.TestSuite()
    for m in _testmodules:
        s = base.autogenerate_testsuite(m.__dict__)
        test_suite.addTest(s)
    return test_suite

#==============================================================================#

#__all__ = ['suite', 'views', 'templatetags', 'models', 'email', 'base', 'helpers']

