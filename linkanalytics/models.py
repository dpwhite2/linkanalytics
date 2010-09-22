from django.db import models
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
#from django.db.models import F

import uuid
import datetime

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
        ##return TrackedUrlInstance.objects.filter(trackee=self.pk)
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
                        

class TrackedUrl(models.Model):
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    #targets =   models.ManyToManyField(TrackedUrlTarget, through='UrlTargetPair')
    trackees =  models.ManyToManyField(Trackee, through='TrackedUrlInstance')
    
    def __unicode__(self):
        return u'%s'%self.name
    
    def url_instances(self):
        return self.trackedurlinstance_set.all()
        
    def url_instances_read(self):
        #return self.trackedurlinstance_set.filter(access_count__gt=0)
        #return self.trackedurlinstance_set.filter(trackedurlaccess__count__gt=0)
        return self.trackedurlinstance_set.annotate(num_accesses=models.Count('trackedurlaccess__count')).filter(num_accesses__gt=0)
        
        # instances containing TrackedUrlAccesses with a count value at least 1
                
    def add_trackee(self, trackee):
        i = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        i.save()
        return i


def _create_uuid():
    return uuid.uuid4().hex
    

class Accessed(object):
    """Class that simplifies cancelling TrackedUrlInstance accesses."""
    # TODO: consider concurrency issues... 
    #   What if another access happens between __init__() and undo()?
    def __init__(self, instance):
        self.instance = instance
        # Save the current 'last_access' in case the new access must be undone
        self.last_access = self.instance.recent_access
        
        self.instance.access_count += 1
        
        today = datetime.date.today()
        if not self.instance.first_access:
            self.instance.first_access = today
        self.instance.recent_access = today
        self.instance.save()
        
    def undo(self):
        # Roll back changes
        self.instance.access_count -= 1
        
        # Only write first_access if this was the "first_access"
        if self.instance.access_count==0:
            self.instance.first_access = None
        self.instance.recent_access = self.last_access
        self.instance.save()
        

class TrackedUrlInstance(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    trackee =       models.ForeignKey(Trackee)
    uuid =          models.CharField(max_length=32, editable=False, default=_create_uuid, unique=True)
    
    notified =      models.DateField(null=True, blank=True)
    #first_access =  models.DateField(null=True, blank=True)
    #recent_access = models.DateField(null=True, blank=True)
    #access_count =  models.IntegerField(default=0)
    
    class Meta:
        unique_together = (("trackedurl", "trackee", ),)
        
    #def __init__(self, *args, **kwargs):
    #    super(TrackedUrlInstance, self).__init__(self, *args, **kwargs)
        
    
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
    url = models.CharField(max_length=3000) # TODO: make this length a configurable setting?
        
#==============================================================================#
# Extras:

class EmailAlreadySentError(Exception):
    """An attempt was made to send a DraftEmail object that was already sent."""
    
class Email(models.Model):
    fromemail =     models.EmailField()
    trackedurl =    models.ForeignKey(TrackedUrl)
    subject =       models.CharField(max_length=256)
    txtmsg =        models.TextField()
    htmlmsg =       models.TextField()
    
def sendemail(email, recipients):
    trackedurls,htmltemplate,txttemplate = parse_email_message(email.message)
    subjtemplate = parse_subject(email.subject)
    msgs = []
    for recipient in recipients:
        subj = subjtemplate.process(recipient)
        html = htmltemplate.process(recipient)
        txt = txttemplate.process(recipient)
        msg = django.core.mail.EmailMultiAlternatives(subj, txt, email.fromemail, [recipient])
        msg.attach_alternative(html, "text/html")
        msgs.append(msg)
    
    cx = django.core.mail.get_connection()
    cx.send_messages(msgs)
    
    #e = Email(fromemail=self.fromemail, subject=self.subject, message=self.message)
    email.trackedurls.add(*trackedurls)
    email.save()
    
    r = EmailRecipients(email=email, datesent=datetime.date.today())
    r.recipients.add(self.pending_recipients)
    r.save()
    

class DraftEmail(models.Model):
    # An Email object is created when the EmailDraft is sent.  At that point, the EmailDraft may not be modified.
    # Also when sent, pending_recipients is flushed to SentEmail.recipients
    pending_recipients = models.ManyToManyField(Trackee)
    fromemail =     models.EmailField()
    subject =       models.CharField(max_length=256)
    message =       models.TextField()
    sent =          models.BooleanField(default=False)
    
    def send(self):
        # This method is under construction.
        if self.sent:
            raise EmailAlreadySentError()
        recipients = parse_recipients(self.pending_recipients)
        e = Email(fromemail=self.fromemail, subject=self.subject, message=self.message)
        sendemail(e, recipients)
        
        self.pending_recipients.clear()
        self.sent = True
    
class EmailRecipients(models.Model):
    email =         models.ForeignKey(Email)
    recipients =    models.ManyToManyField(Trackee)
    datesent =      models.DateField()














