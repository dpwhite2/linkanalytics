from django.db import models
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
#from django.db.models import F

import uuid
import datetime
import itertools
import re

from linkanalytics import email as la_email
from linkanalytics import app_settings

#==============================================================================#

def validate_onezero(value):
    if not (1<=value<=0):
        return ValidationError(u'%s is not 0 or 1.' % value)

#==============================================================================#
# Design:
#
# A *TrackedUrl* represents a url whose accesses are tracked.

# Each TrackedUrl is associated with zero or more *TrackedUrlInstances*.  Each of
# those instances tracks when a single user accesses a single url.  A
# TrackedUrlInstance is associated with exactly one TrackedUrl and one user.

# A *Trackee* is the actor whose url accesses are tracked.  Trackees and
# TrackedUrls have a many-to-many relationship through the TrackedUrlInstance
# class.

# Trackees and TrackedUrls are created by the administrator.
# TrackedUrlInstances are created by the application when a Trackee is assigned
# to a TrackedUrl.


class Trackee(models.Model):
    username =          models.CharField(max_length=64, unique=True)
    first_name =        models.CharField(max_length=64, blank=True)
    last_name =         models.CharField(max_length=64, blank=True)
    emailaddress =      models.EmailField(blank=True)
    comments =          models.TextField(blank=True)
    # If this is a user in the Django auth. system, use his info
    is_django_user =    models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s'%self.username

    def url_instances(self):
        return self.trackedurlinstance_set.all()
    def urls(self):
        return self.trackedurl_set.all()

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
    """Convert a string of emails to a list of trackees and a list of unrecognized emails."""
    parts = _re_emailsplit.split(s)
    for em in parts:
        m = _re_email.match(em)
    pass


class TrackedUrl(models.Model):
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    trackees =  models.ManyToManyField(Trackee, through='TrackedUrlInstance')

    def __unicode__(self):
        return u'%s'%self.name

    def url_instances(self):
        return self.trackedurlinstance_set.all()

    def url_instances_read(self):
        # instances containing TrackedUrlAccesses with a count value at least 1
        return self.trackedurlinstance_set.annotate(num_accesses=models.Count('trackedurlaccess__count')).filter(num_accesses__gt=0)


    def add_trackee(self, trackee):
        i = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        i.save()
        return i


def _create_uuid():
    return uuid.uuid4().hex


class TrackedUrlInstance(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    trackee =       models.ForeignKey(Trackee)
    uuid =          models.CharField(max_length=32, editable=False, default=_create_uuid, unique=True)
    notified =      models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (("trackedurl", "trackee", ),)

    def __unicode__(self):
        return u'%s, %s'%(self.trackedurl, self.trackee)

    def was_accessed(self):
        return self.access_count > 0

    def on_access(self, success, url):
        """success: boolean that indicates if URL access occurred with no errors
           url: the url used (*not* the url redirected to)
        """
        count = 0
        time = None
        if success:
            count = 1
            time = datetime.datetime.now()
        a = TrackedUrlAccess(instance=self, time=time, count=count, url=url)
        a.save()

    def _first_access(self):
        ag = self.trackedurlaccess_set.aggregate(models.Min('time'))
        return ag['time__min']
    def _recent_access(self):
        ag = self.trackedurlaccess_set.aggregate(models.Max('time'))
        return ag['time__max']
    def _access_count(self):
        r = self.trackedurlaccess_set.aggregate(models.Sum('count'))['count__sum']
        return r  if r else  0  # handles case where r is None

    first_access = property(_first_access)
    recent_access = property(_recent_access)
    access_count = property(_access_count)


class TrackedUrlAccess(models.Model):
    instance = models.ForeignKey(TrackedUrlInstance)
    time = models.DateTimeField(null=True, blank=True)
    # should always be 0 or 1.  Zero indicates an error occurred while accessing the URL
    count = models.IntegerField(default=0, validators=[validate_onezero])
    url = models.CharField(max_length=3000, blank=True) # TODO: make this length a configurable setting?

#==============================================================================#
# Extras:

class EmailAlreadySentError(Exception):
    """An attempt was made to send a DraftEmail object that was already sent."""

def _create_trackedurl_for_email():
    u = TrackedUrl(name='_email_{0}'.format(_create_uuid()))
    u.save()
    return u

class Email(models.Model):
    fromemail =     models.EmailField(blank=True)
    trackedurl =    models.ForeignKey(TrackedUrl, editable=False)
    subject =       models.CharField(max_length=256, editable=False)
    txtmsg =        models.TextField(editable=False)
    htmlmsg =       models.TextField(editable=False)

    def send(self, recipients):
        if not recipients or not recipients.exists():
            return
        # Note: msgs = list of django.core.mail.EmailMultiAlternatives
        msgs = list(
                self._create_multipart_email(text,html,recipient)
                for (recipient,(text,html))
                in itertools.izip(recipients, self._instantiate_emails(recipients))
                )

        r = EmailRecipients(email=self, datesent=datetime.date.today())
        r.save()
        for recipient in recipients:
            r.recipients.add(recipient)
        r.save()

        cx = mail.get_connection()
        cx.send_messages(msgs)

    def _create_multipart_email(self, text, html, recipient):
        msg = mail.EmailMultiAlternatives(
                                self.subject, text, self.fromemail,
                                [recipient.emailaddress]
                                )
        msg.attach_alternative(html, "text/html")
        return msg

    def _instantiate_emails(self, recipients):
        """Returns an iterator over (text,html) pairs."""
        urlbase = app_settings.URLBASE
        return la_email.instantiate_emails(
                            self.txtmsg, self.htmlmsg, urlbase,
                            self._generate_urlinstances(recipients)
                            )

    def _generate_urlinstances(self, recipients):
        """Returns an iterator over the uuids of newly created UrlInstances."""
        for recipient in recipients:
            t = TrackedUrlInstance(trackedurl=self.trackedurl, trackee=recipient)
            t.save()
            yield t.uuid
            
    def htmlmsg_brief(self):
        return self.htmlmsg.splitlines()[0]
    htmlmsg_brief.short_description = 'Message (HTML)'


class DraftEmail(models.Model):
    # An Email object is created when the EmailDraft is sent.  At that point, the EmailDraft may not be modified.
    # Also when sent, pending_recipients is flushed to SentEmail.recipients
    pending_recipients = models.ManyToManyField(Trackee, blank=True)
    fromemail =     models.EmailField(blank=True)
    subject =       models.CharField(max_length=256, blank=True)
    message =       models.TextField(blank=True)
    sent =          models.BooleanField(default=False)
    pixelimage =    models.BooleanField(default=False)

    def __unicode__(self):
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
        email_model = self._compile(**kwargs)
        email_model.save()
        email_model.send(self.pending_recipients.all())

        self.pending_recipients.clear()
        self.sent = True
        self.save()
        return email_model

    def _compile(self, **kwargs):
        if not self.subject:
            self.subject = '[No Subject]'
        text,html = la_email.compile_email(self.message, **kwargs)
        u = _create_trackedurl_for_email()
        email_model = Email( fromemail=self.fromemail, trackedurl=u,
                             subject=self.subject, txtmsg=text, htmlmsg=html )

        return email_model
        
    def message_brief(self):
        return self.message.splitlines()[0]
    message_brief.short_description = 'Message'


class EmailRecipients(models.Model):
    email =         models.ForeignKey(Email)
    recipients =    models.ManyToManyField(Trackee)
    datesent =      models.DateField()















