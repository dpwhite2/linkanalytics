import datetime

from django.db import models
from django.core import mail
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance
from linkanalytics.models import TrackedUrlAccess, _create_uuid
from linkanalytics.email import _email
from linkanalytics import app_settings

#==============================================================================#
# Extras:

class EmailAlreadySentError(Exception):
    """An attempt was made to send a DraftEmail object that was already sent."""

def _create_trackedurl_for_email():
    """Creates a TrackedUrl to be used with a new email message."""
    u = TrackedUrl(name='_email_{0}'.format(_create_uuid()))
    u.save()
    return u

class Email(models.Model):
    """Represents a *sent* email message.  This object may not be edited, 
       except to add more recipients.  Its message, subject, from-email, 
       etc, however, may not be modified."""
    fromemail =     models.EmailField(blank=True)
    trackedurl =    models.ForeignKey(TrackedUrl, editable=False)
    subject =       models.CharField(max_length=256, editable=False)
    txtmsg =        models.TextField(editable=False)
    htmlmsg =       models.TextField(editable=False)
    
    class Meta:
        app_label = 'linkanalytics'

    
    def read_count(self):
        """Returns the number of recipients who have read this email."""
        return self.trackedurl.url_instances_read().count()
    
    def unread_count(self):
        """Returns the number of recipients who have not read this email."""
        return self.trackedurl.url_instances_unread().count()
        
    def recipient_count(self):
        """Returns the number of recipients of this email."""
        return self.trackedurl.url_instances().count()

    def send(self, recipients):
        """Attempt to send the email.  This may be called on emails that have 
           already been sent.
        
           recipients: A sequence of Trackee objects who will be sent this 
                       message.
        """
        if not recipients or not recipients.exists():
            return
        urlbase = app_settings.URLBASE
        einstantiator = _email.email_instantiator(self.txtmsg, self.htmlmsg, 
                                                    urlbase)
        
        # Note: msgs = list of django.core.mail.EmailMultiAlternatives
        msgs = []
        cx = mail.get_connection()
        
        # Build the emails
        for recipient in recipients:
            i = TrackedUrlInstance(trackedurl=self.trackedurl, 
                                   trackee=recipient)
            i.save()
            text, html = einstantiator(i.uuid)
            
            msg = self._create_multipart_email(text, html, recipient, cx)
            msgs.append((msg, i, recipient,))
        
        rs = []  # recipients to whom the email was sent
        today = datetime.date.today()
        
        # Send the emails
        cx.open()
        try:
            for msg, i, rec in msgs:
                msg.send()
                i.notified = today
                i.save()
                rs.append(rec)
        finally:
            cx.close()  # Close the connection!
            
            # Record the recipients
            er = EmailRecipients(email=self, datesent=today)
            er.save()
            for recipient in rs:
                er.recipients.add(recipient)
            er.save()
        

    def _create_multipart_email(self, text, html, recipient, connection=None):
        """Creates an email addressed to the given recipient and containing 
           both the given html and text content."""
        msg = mail.EmailMultiAlternatives(
                                self.subject, text, self.fromemail,
                                [recipient.emailaddress],
                                connection=connection
                                )
        msg.attach_alternative(html, "text/html")
        return msg
            
    def htmlmsg_brief(self):
        """A brief representation of the email message.  Currently, this only 
           returns the first line."""
        return self.htmlmsg.splitlines()[0]
    htmlmsg_brief.short_description = 'Message (HTML)'


class DraftEmail(models.Model):
    """An email which has *not* yet been sent.  A DraftEmail object is 
       converted to an Email object when it is sent.  After that, the 
       DraftEmail object may not be modified, and its pending_recipients become 
       the first recipients of the Email message."""
       
    pending_recipients = models.ManyToManyField(Trackee, blank=True)
    fromemail =     models.EmailField(blank=True)
    subject =       models.CharField(max_length=256, blank=True)
    message =       models.TextField(blank=True)
    sent =          models.BooleanField(default=False)
    pixelimage =    models.BooleanField(default=False)
    
    htmlheader =    models.FilePathField(path=app_settings.EMAIL_HEADERSDIR,
                                   match=r'.*\.html',max_length=255,blank=True)
    htmlfooter =    models.FilePathField(path=app_settings.EMAIL_FOOTERSDIR,
                                   match=r'.*\.html',max_length=255,blank=True)
    textheader =    models.FilePathField(path=app_settings.EMAIL_HEADERSDIR,
                                   match=r'.*\.txt',max_length=255,blank=True)
    textfooter =    models.FilePathField(path=app_settings.EMAIL_FOOTERSDIR,
                                   match=r'.*\.txt',max_length=255,blank=True)
    
    class Meta:
        app_label = 'linkanalytics'

    def __unicode__(self):
        """Returns a unicode representation of a DraftEmail."""
        n = self.pending_recipients.count()
        lim = min(n, 5)
        rec = u','.join(unicode(a) for a in self.pending_recipients.all()[:lim])
        if n >= 5:
            rec += u',...'
        elif n == 0:
            rec = u'[none]'
        sent = ''
        if self.sent:
            sent = '(SENT)'
        return u'"{0}": to {1}.  {2}'.format(self.subject, rec, sent)

    def send(self, **kwargs):
        """Send a DraftEmail to the pending_recipients.  Once sent the first
           time, the DraftEmail may not be sent again.  Instead, use the send
           method on Email.
        """
        if self.sent:
            raise EmailAlreadySentError()
        if self.pixelimage:
            kwargs['pixelimage_type'] = 'png'
        if self.htmlheader:
            with open(self.htmlheader) as f:
                kwargs['html_header'] = f.read()
        if self.htmlfooter:
            with open(self.htmlfooter) as f:
                kwargs['html_footer'] = f.read()
        if self.textheader:
            with open(self.textheader) as f:
                kwargs['text_header'] = f.read()
        if self.textfooter:
            with open(self.textfooter) as f:
                kwargs['text_footer'] = f.read()
        email_model = self._compile(**kwargs)
        email_model.save()
        email_model.send(self.pending_recipients.all())

        self.pending_recipients.clear()
        self.sent = True
        self.save()
        return email_model

    def _compile(self, **kwargs):
        """Compile the DraftEmail object into an Email object.  Do not call 
           directly, instead use send().
        """
        if not self.subject:
            self.subject = app_settings.EMAIL_DEFAULT_SUBJECT
        text, html = _email.compile_email(self.message, **kwargs)
        u = _create_trackedurl_for_email()
        email_model = Email( fromemail=self.fromemail, trackedurl=u,
                             subject=self.subject, txtmsg=text, htmlmsg=html )

        return email_model
        
    def message_brief(self):
        """A brief representation of the email message.  Currently, this only 
           returns the first line."""
        lines =  self.message.splitlines()
        if lines:
            return lines[0]
        else:
            return ""
    message_brief.short_description = 'Message'


class EmailRecipients(models.Model):
    """A collection of Trackees to whom an Email has been sent.  Whenever an 
       Email is sent, its recipients are added to a new EmailRecipients object.  
       Therefore, a single Email may be associated with more than one 
       EmailRecipients object.
    """
    email =         models.ForeignKey(Email)
    recipients =    models.ManyToManyField(Trackee)
    datesent =      models.DateField()
    
    class Meta:
        app_label = 'linkanalytics'


#==============================================================================#


