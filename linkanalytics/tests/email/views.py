"""
    Tests for normal views as well as targetviews.
"""

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import TrackedUrlInstance, Trackee
from linkanalytics.email.models import Email, DraftEmail

from .. import base

#==============================================================================#
# Email view tests:

class ViewEmailMain_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    def test_contacts_count(self):
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no trackees
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 0)
            
            # Case 2: one trackee with an email
            t = Trackee(username='withemail', emailaddress='user0@example.com')
            t.save()
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 1)
            
            # Case 3: one trackee with and one without an email
            t = Trackee(username='withoutemail')
            t.save()
            response = self.client.get(url)
            self.assertEquals(response.context['contact_count'], 1)
            
    def test_draft_count(self):
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no drafts
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 0)
            
            # Case 2: one unsent draft
            e = DraftEmail()
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 1)
            
            # Case 3: first two unsent drafts, then one unsent draft and one 
            #         sent draft
            e = DraftEmail()
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 2)
            e.sent = True
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['draft_count'], 1)
            
    def test_sent_count(self):
        u = self.new_trackedurl('trackedurl')
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-main')
            # Case 1: no emails
            response = self.client.get(url)
            self.assertEquals(response.context['sent_count'], 0)
            
            # Case 2: one sent email
            e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
            e.save()
            response = self.client.get(url)
            self.assertEquals(response.context['sent_count'], 1)
        
    
class ComposeEmail_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    def test_basic_edit(self):
        # Very basic test... just see that url exists.
        e = DraftEmail()
        e.save()
        id = e.pk
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-idcompose', 
                             kwargs={'emailid':id})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    # Check that the 'To:' field is resolved to the correct emails
    def test_to_existingEmailAddress(self):
        # A valid existing email address
        self.create_users(1)
        t = Trackee(username='trackee', emailaddress='trackee@example.com')
        t.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            data = {'do_save':'', 'to':'trackee@example.com', 
                    'message':'Message.'}
            response = self.client.post(url, data)
            
            self.assertEquals(response.status_code, 302)
            
            qs = DraftEmail.objects.all()
            self.assertEquals(qs.count(), 1)
            draft = qs[0]
            self.assertEquals(draft.pending_recipients.count(), 1)
            self.assertEquals(draft.pending_recipients.all()[0].emailaddress, 
                              'trackee@example.com')
        
    def test_to_existingUsername(self):
        # A valid existing username
        self.create_users(1)
        t = Trackee(username='trackee', emailaddress='trackee@example.com')
        t.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            data = {'do_save':'', 'to':'trackee', 'message':'Message.'}
            response = self.client.post(url, data)
            
            self.assertEquals(response.status_code, 302)
            
            qs = DraftEmail.objects.all()
            self.assertEquals(qs.count(), 1)
            draft = qs[0]
            self.assertEquals(draft.pending_recipients.count(), 1)
            self.assertEquals(draft.pending_recipients.all()[0].username, 
                              'trackee')
                              
    def test_to_nonExistentUsername(self):
        # A valid but non-existent username
        self.create_users(1)
        t = Trackee(username='trackee', emailaddress='trackee@example.com')
        t.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            data = {'do_save':'', 'to':'badtrackee', 'message':'Message.'}
            response = self.client.post(url, data)
            
            self.assertEquals(response.status_code, 200)
            
            qs = DraftEmail.objects.all()
            self.assertEquals(qs.count(), 1)
            draft = qs[0]
            self.assertEquals(draft.pending_recipients.count(), 0)
    
    def test_to_nonExistentEmailaddress(self):
        # A valid but non-existent email
        self.create_users(1)
        t = Trackee(username='trackee', emailaddress='trackee@example.com')
        t.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-compose')
            data = {'do_save':'', 'to':'other@example.com', 
                    'message':'Message.'}
            response = self.client.post(url, data)
            
            self.assertEquals(response.status_code, 302)
            
            qs = DraftEmail.objects.all()
            self.assertEquals(qs.count(), 1)
            draft = qs[0]
            self.assertEquals(draft.pending_recipients.count(), 1)
            self.assertEquals(draft.pending_recipients.all()[0].emailaddress, 
                              'other@example.com')
    
    # Hidden pixel
    # Headers and Footers
    # Save button
    # Send button
    
class ViewSentEmails_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        # When no emails exist
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewsent')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(len(response.context['emails']), 0)
            
    def test_draftNotSent(self):
        # When an email is drafted, but not sent
        self.create_users(1)
        e = DraftEmail()
        e.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewsent')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(len(response.context['emails']), 0)
    
    def test_oneSent(self):
        # When an email was sent
        self.create_users(1)
        u = self.new_trackedurl('trackedurl')
        e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
        e.save()
        id = e.pk
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewsent')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(len(response.context['emails']), 1)
            self.assertEquals(response.context['emails'][0].pk, id)
    
    def test_multiSent(self):
        # When multiple emails were sent
        self.create_users(1)
        def sendEmail():
            u = self.new_trackedurl('trackedurl')
            e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
            e.save()
            return e.pk
        ids = [sendEmail() for i in range(3)]
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewsent')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(len(response.context['emails']), 3)
            pks = [response.context['emails'][i].pk for i in range(3)]
            pks.sort()
            self.assertEquals(ids, pks)
    
class ViewDraftEmails_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewdrafts')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    # When no emails exist
    # When an email has been set (and should no longer be a draft)
    # When one unsent email draft exists
    # When multi unsent email drafts exist
    
class ViewEmailRead_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        u = self.new_trackedurl('trackedurl')
        e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
        e.save()
        id = e.pk
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewread', 
                             kwargs={'emailid': id})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
            itemiter = response.context['items']
            items = list(itemiter)
            self.assertEquals(len(items), 0)
            
    # Check email read
    # Check one email read and one not read
    # Check multiple emails read
    # what if the given email id does not exist?
            
class ViewEmailUnread_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        u = self.new_trackedurl('trackedurl')
        e = Email(trackedurl=u, subject='X', txtmsg='Y', htmlmsg='Z')
        e.save()
        id = e.pk
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewunread', 
                             kwargs={'emailid':id})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    # what if the given email id does not exist?
    
class CreateEmailContact_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-createcontact')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
    
    def test_basic_editExisting(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        t = Trackee(username='trackee', emailaddress='me@example.com')
        t.save()
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-editcontact', 
                             kwargs={'username':'trackee'})
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            
    # Edit existing but username doesn't exist
    # Username is duplicate
    # no email address given
    # Valid name and email
    # Save button
    
class ViewEmailContacts_TestCase(base.LinkAnalytics_DBTestCaseBase):
    def test_basic(self):
        # Very basic test... just see that url exists.
        self.create_users(1)
        with self.scoped_login('user0', 'password'):
            url = urlreverse('linkanalytics-email-viewcontacts')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
    
    # No contacts
    # One contact
    # Multi contacts

#==============================================================================#
