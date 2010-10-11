from linkanalytics.tests import base
from linkanalytics.tests import helpers

#==============================================================================#
# Test modules...
from linkanalytics.tests.email import views, models, email

# List of all test modules containing tests.  
_testmodules = [views, models, email]

# Import all test cases so they appear in this module.  This appears to be 
# needed for Hudson automated testing.
for m in _testmodules:
    for name,val in m.__dict__.iteritems():
        if name.endswith('_TestCase') and \
           issubclass(val, base.LinkAnalytics_TestCaseBase):
            globals()[name] = val
