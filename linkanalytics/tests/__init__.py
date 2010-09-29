import unittest

from . import base

#==============================================================================#
# Test modules...
##from . import views
##from . import templatetags
##from . import models
##from . import email
from linkanalytics.tests import views, templatetags, models, email
#from linkanalytics.tests import templatetags
#from linkanalytics.tests import models
#from linkanalytics.tests import email

#==============================================================================#
# List of all test modules containing tests.  
_testmodules = [views,templatetags,models,email]

def suite():
    test_suite = unittest.TestSuite()
    for m in _testmodules:
        s = base.autogenerate_testsuite(m.__dict__)
        test_suite.addTest(s)
    return test_suite

#==============================================================================#

__all__ = ['suite', 'views', 'templatetags', 'models', 'email']

