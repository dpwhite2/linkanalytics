from django.db import models
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError, ObjectDoesNotExist

#from django.db.models import F

import uuid
import datetime
import itertools
import re

from linkanalytics import email as la_email
from linkanalytics import app_settings

#==============================================================================#

def validate_onezero(value):
    """The given value must be a 1 or a 0.  If it is not, Django's 
       ValidationError is raised.
    """
    if not (1<=value<=0):
        return ValidationError(u'%s is not 0 or 1.' % value)

#==============================================================================#
# Design:
#
# A *TrackedUrl* represents a url whose accesses are tracked.

# Each TrackedUrl is associated with zero or more *TrackedUrlInstances*.  Each 
# of those instances tracks when a single user accesses a single url.  A
# TrackedUrlInstance is associated with exactly one TrackedUrl and one user.

# A *Trackee* is the actor whose url accesses are tracked.  Trackees and
# TrackedUrls have a many-to-many relationship through the TrackedUrlInstance
# class.

# Trackees and TrackedUrls are created by the administrator.
# TrackedUrlInstances are created by the application when a Trackee is assigned
# to a TrackedUrl.


class Trackee(models.Model):
    """The 'actor' whose visits to particular URLs are tracked by 
       Linkanalytics.  One Trackee may be tracked through any number of URLs. 
    """
    username =          models.CharField(max_length=64, unique=True)
    first_name =        models.CharField(max_length=64, blank=True)
    last_name =         models.CharField(max_length=64, blank=True)
    emailaddress =      models.EmailField(blank=True)
    comments =          models.TextField(blank=True)
    # If this is a user in the Django auth. system, use his info
    is_django_user =    models.BooleanField(default=False)

    def __unicode__(self):
        """Returns a unicode representation of a Trackee."""
        return u'%s'%self.username

    # pylint: disable=E1101
    def url_instances(self):
        """A QuerySet of all TrackedUrlInstances which link to this Trackee."""
        return self.trackedurlinstance_set.all()
    def urls(self):
        """A QuerySet of all TrackedUrls which link to this Trackee."""
        return self.trackedurl_set.all()
    # pylint: enable=E1101
    
    @staticmethod
    def from_django_user(djuser, comments=""):
        """Create a Trackee from the given Django User object."""
        assert isinstance(djuser, User)
        return Trackee( username=       djuser.username,
                        first_name=     djuser.first_name,
                        last_name=      djuser.last_name,
                        emailaddress=   djuser.email,
                        comments=       comments,
                        is_django_user= True )
                        
    

_EMAILLC = r'[-\w\d!#$%&\'*+/=?^_`{|}~]'
_EMAILLC2 = r'[-\w\d!#$%&\'*+/=?^_`{|}~.]'  # Note: contains a period
_EMAILLOCAL = _EMAILLC+r'(?:'+_EMAILLC2+_EMAILLC+r'|'+_EMAILLC+r')*'
_EMAILDOMAIN = r'[-\w\d.]+'
_EMAIL = _EMAILLOCAL+r'@'+_EMAILDOMAIN
_re_email = re.compile(_EMAIL)
_re_emailsplit = re.compile(r'[\s,]+')

def resolve_emails(s):
    """Convert a string of emails to a list of trackees and a list of 
       unrecognized emails."""
    parts = _re_emailsplit.split(s)
    trackees = set()
    unknown_emails = set()
    unknown_names = set()
    for em in parts:
        if em.find('@')!=-1:
            # this is an email address
            qs = Trackee.objects.filter(emailaddress=email)
            if qs.exists():
                trackees.add(qs[0])
            else:
                unknown_emails.add(em)
        else:
            try:
                trackees.add(Trackee.objects.get(username=em))
            except ObjectDoesNotExist:
                unknown_names.add(em)
    return { 'trackees':trackees, 'unknown_emails':unknown_emails, 
             'unknown_names':unknown_names }


class TrackedUrl(models.Model):
    """A group of urls whose accesses are tracked by LinkAnalytics.  The 
       TrackedUrl object is *not* the same as the physical URL which is 
       accessed.  Instead, a unique id is associated with a 
       (TrackedUrl, Trackee) pair--whenever that unique id is accessed, the 
       Trackee is considered to have accessed the TrackedUrl.  This places no 
       restrictions on where the Trackee is redirected to after the access.
    """
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    trackees =  models.ManyToManyField(Trackee, through='TrackedUrlInstance')

    def __unicode__(self):
        """Returns a unicode representation of a TrackedUrl."""
        return u'%s'%self.name

    # pylint: disable-msg=E1101
    def url_instances(self):
        """A QuerySet of all TrackedUrlInstances associated with this 
           TrackedUrl"""
        return self.trackedurlinstance_set.all()

    def url_instances_read(self):
        """A QuerySet of all TrackedUrlInstances associated with this 
           TrackedUrl which have been accessed (or 'read')."""
        # instances containing TrackedUrlAccesses with a count value at least 1
        return self.trackedurlinstance_set.annotate(
                        num_accesses=models.Count('trackedurlaccess__count')
                    ).filter(num_accesses__gt=0)

    def url_instances_unread(self):
        """A QuerySet of all TrackedUrlInstances associated with this 
           TrackedUrl which have not been accessed (or 'not read')."""
        return self.trackedurlinstance_set.annotate(
                        num_accesses=models.Count('trackedurlaccess__count')
                    ).filter(num_accesses=0)
    # pylint: enable-msg=E1101

    def add_trackee(self, trackee):
        """Creates a TrackedUrlInstance associating the given Trackee with this 
           TrackedUrl.  The TrackedUrlInstance is saved and returned."""
        i = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        i.save()
        return i


def _create_uuid():
    """Returns a 32-character string containing a randomly-generated UUID."""
    return uuid.uuid4().hex


class TrackedUrlInstance(models.Model):
    """The class which links a Trackee and a TrackedUrl.  It is through this 
       class (and owned objects) that access statistics are kept."""
    trackedurl =    models.ForeignKey(TrackedUrl)
    trackee =       models.ForeignKey(Trackee)
    uuid =          models.CharField(max_length=32, editable=False, 
                                     default=_create_uuid, unique=True)
    notified =      models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (("trackedurl", "trackee", ),)

    def __unicode__(self):
        """Returns a unicode representation of a TrackedUrlInstance."""
        return u'%s, %s'%(self.trackedurl, self.trackee)

    def was_accessed(self):
        """Returns True if this TrackedUrlInstance has been accessed; returns 
           False otherwise."""
        return self.access_count > 0

    def on_access(self, success, url):
        """Call to indicate that the TrackedUrlInstance has been accessed.  
           This is usually called from within a view function.
            
           success: boolean that indicates if URL access occurred with no errors
           url: the url used (*not* the url redirected to)
        """
        count = 0
        time = None
        if success:
            count = 1
            time = datetime.datetime.now()
        a = TrackedUrlAccess(instance=self, time=time, count=count, url=url)
        a.save()

    # pylint: disable-msg=E1101
    def _first_access(self):
        ag = self.trackedurlaccess_set.aggregate(models.Min('time'))
        return ag['time__min']
    def _recent_access(self):
        ag = self.trackedurlaccess_set.aggregate(models.Max('time'))
        return ag['time__max']
    def _access_count(self):
        tset = self.trackedurlaccess_set
        r = tset.aggregate(models.Sum('count'))['count__sum']
        return r  if r else  0  # handles case where r is None
    # pylint: enable-msg=E1101
    
    first_access = property(_first_access)
    recent_access = property(_recent_access)
    access_count = property(_access_count)


class TrackedUrlAccess(models.Model):
    """Records a single access (possibly unsuccessful) of the associated 
       TrackedUrlInstance."""
    instance =  models.ForeignKey(TrackedUrlInstance)
    time =      models.DateTimeField(null=True, blank=True)
    # Should always be 0 or 1.  Zero indicates an error occurred while 
    # accessing the URL
    count =     models.IntegerField(default=0, validators=[validate_onezero])
    # TODO: make this length a configurable setting?
    url =   models.CharField(max_length=3000, blank=True) 

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
        einstantiator = la_email.email_instantiator(self.txtmsg, self.htmlmsg, 
                                                    urlbase)
        
        # Note: msgs = list of django.core.mail.EmailMultiAlternatives
        msgs = []
        cx = mail.get_connection()
        
        # Build the emails
        for recipient in recipients:
            i = TrackedUrlInstance(trackedurl=self.trackedurl, 
                                   trackee=recipient)
            i.save()
            text,html = einstantiator(i.uuid)
            
            msg = self._create_multipart_email(text,html,recipient,cx)
            msgs.append((msg, i, recipient,))
        
        rs = []  # recipients to whom the email was sent
        today = datetime.date.today()
        
        # Send the emails
        cx.open()
        try:
            for msg,i,rec in msgs:
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

    def __unicode__(self):
        """Returns a unicode representation of a DraftEmail."""
        n = self.pending_recipients.count()
        lim = min(n,5)
        rec = u','.join(unicode(a) for a in self.pending_recipients.all()[:lim])
        if n>=5:
            rec += u',...'
        elif n==0:
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
            self.subject = '[No Subject]'
        text,html = la_email.compile_email(self.message, **kwargs)
        u = _create_trackedurl_for_email()
        email_model = Email( fromemail=self.fromemail, trackedurl=u,
                             subject=self.subject, txtmsg=text, htmlmsg=html )

        return email_model
        
    def message_brief(self):
        """A brief representation of the email message.  Currently, this only 
           returns the first line."""
        return self.message.splitlines()[0]
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















