import uuid
import datetime
import itertools
import re

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics import app_settings
from linkanalytics import urlex

#==============================================================================#
# These sub packages contain models.py files that must be imported at the end 
# of this file.

_subpackages = ['linkanalytics.email',]

#==============================================================================#
# Django validators

def validate_onezero(value):
    """The given value must be a 1 or a 0.  If it is not, Django's 
       ValidationError is raised.
    """
    if not (1<=value<=0):
        return ValidationError(u'%s is not 0 or 1.' % value)

#==============================================================================#
# Design:
#
# A *Tracker* represents a url whose accesses are tracked.

# Each Tracker is associated with zero or more *TrackedInstances*.  Each 
# of those instances tracks when a single user accesses a single url.  A
# TrackedInstance is associated with exactly one Tracker and one user.

# A *Visitor* is the actor whose url accesses are tracked.  Visitors and
# Trackers have a many-to-many relationship through the TrackedInstance
# class.

# Visitors and Trackers are created by the administrator.
# TrackedInstances are created by the application when a Visitor is assigned
# to a Tracker.

_re_email_username_replace = re.compile(r'[^_\w\d]')

class Visitor(models.Model):
    """The 'actor' whose visits to particular URLs are tracked by 
       Linkanalytics.  One Visitor may be tracked through any number of URLs. 
    """
    username =          models.CharField(max_length=64, unique=True)
    first_name =        models.CharField(max_length=64, blank=True)
    last_name =         models.CharField(max_length=64, blank=True)
    emailaddress =      models.EmailField(blank=True)
    comments =          models.TextField(blank=True)
    # If this is a user in the Django auth. system, use his info
    is_django_user =    models.BooleanField(default=False)

    def __unicode__(self):
        """Returns a unicode representation of a Visitor."""
        return u'%s' % self.username

    def instances(self):
        """A QuerySet of all TrackedInstances which link to this Visitor."""
        return self.trackedinstance_set.all()
    def urls(self):
        """A QuerySet of all Trackers which link to this Visitor."""
        return self.tracker_set.all()
    
    @staticmethod
    def from_django_user(djuser, comments=""):
        """Create a Visitor from the given Django User object."""
        assert isinstance(djuser, User)
        return Visitor( username=       djuser.username,
                        first_name=     djuser.first_name,
                        last_name=      djuser.last_name,
                        emailaddress=   djuser.email,
                        comments=       comments,
                        is_django_user= True )
                        
    @staticmethod
    def from_email(email, comments=""):
        """Create a Visitor from the given email address."""
        basename = _re_email_username_replace.sub('_', email)
        name = basename
        i = 0
        # Append integer until username is unique.
        while Visitor.objects.filter(username=name).exists():
            name = '{0}{1}'.format(basename, i)
            i += 1
        return Visitor( username=       name,
                        emailaddress=   email,
                        comments=       comments )
                        
    @staticmethod
    def unknown():
        """Return the unknown Visitor object.  This is used when recording some 
           failed accesses."""
        try:
            return Visitor.objects.get(username='_UNKNOWN')
        except ObjectDoesNotExist:
            v = Visitor(username='_UNKNOWN')
            v.save()
            return v
    

#_EMAILLC = r'[-\w\d!#$%&\'*+/=?^_`{|}~]'
#_EMAILLC2 = r'[-\w\d!#$%&\'*+/=?^_`{|}~.]'  # Note: contains a period
#_EMAILLOCAL = _EMAILLC+r'(?:'+_EMAILLC2+_EMAILLC+r'|'+_EMAILLC+r')*'
#_EMAILDOMAIN = r'[-\w\d.]+'
#_EMAIL = _EMAILLOCAL+r'@'+_EMAILDOMAIN
#_re_email = re.compile(_EMAIL)
#_re_emailsplit = re.compile(r'[\s,]+')

def resolve_emails(parts):
    """Convert a sequence of emails and/or usernames into Visitors."""
    trackees = set()
    unknown_emails = set()
    for em in parts:
        if em.find('@')!=-1:
            # this is an email address
            qs = Visitor.objects.filter(emailaddress=em)
            if qs.exists():
                trackees.add(qs[0])
            else:
                t = Visitor.from_email(em)
                t.save()
                trackees.add(t)
        else:
            # The ComposeEmail form validates usernames, so the following 
            # should never raise an ObjectDoesNotExist exception.
            trackees.add(Visitor.objects.get(username=em))
    return { 'trackees':trackees, 'unknown_emails':unknown_emails }
    
def _create_uuid():
    """Returns a 32-character string containing a randomly-generated UUID."""
    return uuid.uuid4().hex

    
class Tracker(models.Model):
    """A group of urls whose accesses are tracked by LinkAnalytics.  The 
       Tracker object is *not* the same as the physical URL which is 
       accessed.  Instead, a unique id is associated with a 
       (Tracker, Visitor) pair--whenever that unique id is accessed, the 
       Visitor is considered to have accessed the Tracker.  This places no 
       restrictions on where the Visitor is redirected to after the access.
    """
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    visitors =  models.ManyToManyField(Visitor, through='TrackedInstance')

    def __unicode__(self):
        """Returns a unicode representation of a Tracker."""
        return u'%s' % self.name

    def instances(self):
        """A QuerySet of all TrackedInstances associated with this 
           Tracker"""
        return self.trackedinstance_set.all()

    def instances_read(self):
        """A QuerySet of all TrackedInstances associated with this 
           Tracker which have been accessed (or 'read')."""
        # instances containing Accesses with a count value at least 1
        return self.trackedinstance_set.annotate(
                        num_accesses=models.Count('access__count')
                    ).filter(num_accesses__gt=0)

    def instances_unread(self):
        """A QuerySet of all TrackedInstances associated with this 
           Tracker which have not been accessed (or 'not read')."""
        return self.trackedinstance_set.annotate(
                        num_accesses=models.Count('access__count')
                    ).filter(num_accesses=0)

    def add_visitor(self, visitor):
        """Creates a TrackedInstance associating the given Visitor with this 
           Tracker.  The TrackedInstance is saved and returned."""
        i = TrackedInstance(tracker=self, visitor=visitor)
        i.save()
        return i
                        
    @staticmethod
    def unknown():
        """Return the unknown Tracker object.  This is used when recording some 
           failed accesses."""
        try:
            return Tracker.objects.get(name='_UNKNOWN')
        except ObjectDoesNotExist:
            t = Tracker(name='_UNKNOWN')
            t.save()
            return t
        


class TrackedInstance(models.Model):
    """The class which links a Visitor and a Tracker.  It is through this 
       class (and owned objects) that access statistics are kept."""
    tracker =       models.ForeignKey(Tracker)
    visitor =       models.ForeignKey(Visitor)
    uuid =          models.CharField(max_length=32, editable=False, 
                                     default=_create_uuid, unique=True)
    notified =      models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (("tracker", "visitor", ),)

    def __unicode__(self):
        """Returns a unicode representation of a TrackedInstance."""
        return u'%s, %s' % (self.tracker, self.visitor)

    def was_accessed(self):
        """Returns True if this TrackedInstance has been accessed; returns 
           False otherwise."""
        return self.access_count > 0

    def on_access(self, success, url):
        """Call to indicate that the TrackedInstance has been accessed.  
           This is usually called from within a view function.
            
           success: boolean that indicates if URL access occurred with no errors
           url: the url used (*not* the url redirected to)
        """
        count = 0
        time = datetime.datetime.now()
        if success:
            count = 1
        a = Access(instance=self, time=time, count=count, url=url)
        a.save()

    def _first_access(self):
        """Getter for first_access property.  Returns the Access 
           object representing the first access of this TrackedInstance, or 
           None if it has not yet been accessed.
        """
        ag = self.access_set.filter(count__gte=1).aggregate(models.Min('time'))
        return ag['time__min']
        
    def _recent_access(self):
        """Getter for recent_access property.  Returns the Access 
           object representing the most recent access of this 
           TrackedInstance, or None if it has not yet been accessed.
        """
        ag = self.access_set.filter(count__gte=1).aggregate(models.Max('time'))
        return ag['time__max']
        
    def _access_count(self):
        """Getter for access_count property.  Returns the access count for this 
           TrackedInstance.
        """
        tset = self.access_set
        r = tset.aggregate(models.Sum('count'))['count__sum']
        return r  if r else  0  # handles case where r is None
    
    first_access = property(_first_access)
    recent_access = property(_recent_access)
    access_count = property(_access_count)
            
    def generate_hashedurl(self, urltail):
        """Creates a hashed url appropriate for this TrackedInstance.  The 
           urltail is the portion of the url that will appear after the uuid.
        """
        return urlex.create_hashedurl(self.uuid, urltail)
        
    def generate_hash(self, data):
        """Creates a hash value appropriate for this TrackedInstance.  The 
           data parameter is the value that should appear after the uuid.
        """
        return urlex.generate_urlhash(self.uuid, data)
    
    def match_hash(self, hash, data):
        """Returns True if hash == self.generate_hash(data).  Returns False 
           otherwise.
        """
        newhash = self.generate_hash(data)
        return hash == newhash
        
    @staticmethod
    def unknown():
        """Return the unknown TrackedInstance object.  This is used when 
           recording some failed accesses."""
        v = Visitor.unknown()
        t = Tracker.unknown()
        try:
            return TrackedInstance.objects.get(tracker=t, visitor=v)
        except ObjectDoesNotExist:
            i = TrackedInstance(tracker=t, visitor=v)
            i.save()
            return i
    

class Access(models.Model):
    """Records a single access (possibly unsuccessful) of the associated 
       TrackedInstance."""
    instance =  models.ForeignKey(TrackedInstance)
    time =      models.DateTimeField(null=True, blank=True)
    # Should always be 0 or 1.  Zero indicates an error occurred while 
    # accessing the URL
    count =     models.IntegerField(default=0, validators=[validate_onezero])
    # TODO: make this length a configurable setting?
    url =   models.CharField(max_length=app_settings.URLFIELD_LENGTH, 
                             blank=True)
    

#==============================================================================#
# import models from sub packages

for _pkg in _subpackages:
    __import__(_pkg, fromlist=['models'])

#==============================================================================#











