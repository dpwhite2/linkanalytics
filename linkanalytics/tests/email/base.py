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
        
    def new_draftemail(self, *args, **kwargs):
        """Creates and saves a DraftEmail.  If kwarg 'recipients' is given, it 
           must be an iterable, and its contents will be added to 
           pending_recipients."""
        recipients = []
        if 'recipients' in kwargs:
            recipients.extend(kwargs['recipients'])
            del kwargs['recipients']
        d = DraftEmail(**kwargs)
        d.save()
        for r in recipients:
            d.pending_recipients.add(r)
        return d
        
    def new_email(self, *args, **kwargs):
        """Creates and saves an Email"""
        e = Email(**kwargs)
        e.save()
        return e
        
#==============================================================================#

