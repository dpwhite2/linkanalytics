from linkanalytics.email.models import Email, DraftEmail, EmailRecipients

from linkanalytics.tests import base


#==============================================================================#
class LinkAnalytics_EmailTestCaseBase(base.LinkAnalytics_DBTestCaseBase):
    """Base class for all linkanalytics.email tests involving database access.  
       If the database is not used, LinkAnalytics_TestCaseBase may be used.
    """
    def tearDown(self):
        super(LinkAnalytics_EmailTestCaseBase, self).tearDown()
        
        Email.objects.all().delete()
        DraftEmail.objects.all().delete()
        EmailRecipients.objects.all().delete()
        
#==============================================================================#

