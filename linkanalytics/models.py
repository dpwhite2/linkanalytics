import uuid
import datetime
import itertools
import re
import hashlib
import hmac

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse as urlreverse

#from django.db.models import F


from linkanalytics import app_settings
from linkanalytics import urlex

#==============================================================================#
# These sub packages contain models.py files that must be imported at the end 
# of this file.

_subpackages = ['linkanalytics.email',]

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

_re_email_username_replace = re.compile(r'[^_\w\d]')

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
        return u'%s' % self.username

    def url_instances(self):
        """A QuerySet of all TrackedUrlInstances which link to this Trackee."""
        return self.trackedurlinstance_set.all()
    def urls(self):
        """A QuerySet of all TrackedUrls which link to this Trackee."""
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
                        
    @staticmethod
    def from_email(email, comments=""):
        """Create a Trackee from the given email address."""
        basename = _re_email_username_replace.sub('_', email)
        name = basename
        i = 0
        # Append integer until username is unique.
        while Trackee.objects.filter(username=name).exists():
            name = '{0}{1}'.format(basename, i)
            i += 1
        return Trackee( username=       name,
                        emailaddress=   email,
                        comments=       comments )
    

_EMAILLC = r'[-\w\d!#$%&\'*+/=?^_`{|}~]'
_EMAILLC2 = r'[-\w\d!#$%&\'*+/=?^_`{|}~.]'  # Note: contains a period
_EMAILLOCAL = _EMAILLC+r'(?:'+_EMAILLC2+_EMAILLC+r'|'+_EMAILLC+r')*'
_EMAILDOMAIN = r'[-\w\d.]+'
_EMAIL = _EMAILLOCAL+r'@'+_EMAILDOMAIN
_re_email = re.compile(_EMAIL)
_re_emailsplit = re.compile(r'[\s,]+')

def resolve_emails(parts):
    """Convert a sequence of emails and/or usernames into Trackees."""
    trackees = set()
    unknown_emails = set()
    for em in parts:
        if em.find('@')!=-1:
            # this is an email address
            qs = Trackee.objects.filter(emailaddress=em)
            if qs.exists():
                trackees.add(qs[0])
            else:
                t = Trackee.from_email(em)
                t.save()
                trackees.add(t)
        else:
            # The ComposeEmail form validates usernames, so the following 
            # should never raise an ObjectDoesNotExist exception.
            trackees.add(Trackee.objects.get(username=em))
    return { 'trackees':trackees, 'unknown_emails':unknown_emails }


def generate_hash(data):
    """Generates a hash for the given string.  The return value is a string of 
       hexadecimal digits.
    """
    return hmac.new(app_settings.SECRET_KEY, data, hashlib.sha1).hexdigest()

def _create_uuid():
    """Returns a 32-character string containing a randomly-generated UUID."""
    return uuid.uuid4().hex


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
    secret_id = models.CharField(max_length=32, editable=False,
                                 default=_create_uuid, unique=True)

    def __unicode__(self):
        """Returns a unicode representation of a TrackedUrl."""
        return u'%s' % self.name

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

    def add_trackee(self, trackee):
        """Creates a TrackedUrlInstance associating the given Trackee with this 
           TrackedUrl.  The TrackedUrlInstance is saved and returned."""
        i = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        i.save()
        return i
        
    def add_validator(self, validator_type, value):
        # does a validator with the given type and value already exist?
        qs = self.targetvalidator_set.filter(type=validator_type, value=value)
        if not qs.exists():
            v = TargetValidator(trackedurl=self, type=validator_type, 
                                value=value)
            v.save()
        else:
            v = qs[0]
        return v
        
    def generate_hash(self, data):
        """ Generates a hash for the given string.  The SECRET_KEY and 
            TrackedUrl's secret_id value are both used.  The returned value is 
            a string of hexadecimal digits.
        """
        return generate_hash(data+self.secret_id)
                        
    def match_hash(self, hash, data):
        newhash = self.generate_hash(data)
        return hash == newhash


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
        return u'%s, %s' % (self.trackedurl, self.trackee)

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
    
    first_access = property(_first_access)
    recent_access = property(_recent_access)
    access_count = property(_access_count)
    
    def validate_target(self, url):
        qs = self.trackedurl.targetvalidator_set.all()
        if qs.exists():
            return any( v(url) for v in qs )
        else:
            # Return True explicitly because any() on an empty sequence 
            # returns False.
            return True
            
    def generate_hashedurl(self, urltail):
        if not urltail.startswith('/'):
            urltail = '/%s' % urltail
        hash = self.trackedurl.generate_hash(urltail)
        return urlex.create_hashedurl(hash, self.uuid, urltail)
            
    def generate_hash(self, data):
        return self.trackedurl.generate_hash(data)
        
    def match_hash(self, hash, data):
        return self.trackedurl.match_hash(hash, data)
    

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
    

_VALIDATOR_TYPE_LITERAL = 0
_VALIDATOR_TYPE_REGEX = 1
_VALIDATOR_TYPE_FUNC = 2

_VALIDATOR_TYPES = (
    (_VALIDATOR_TYPE_LITERAL,   'Literal URL'),
    (_VALIDATOR_TYPE_REGEX,     'Regex'),
    (_VALIDATOR_TYPE_FUNC,      'Function'),
    )
    
_targetvalidator_regex_cache = {}

def _get_targetvalidator_regex(s):
    if s not in _targetvalidator_regex_cache:
        _targetvalidator_regex_cache[s] = re.compile(s)
    return _targetvalidator_regex_cache[s]
        
    
class TargetValidator(models.Model):
    """"""
    trackedurl = models.ForeignKey(TrackedUrl)
    type =       models.IntegerField(choices=_VALIDATOR_TYPES)
    value =      models.CharField(max_length=3000)
    
    def __call__(self, url):
        if self.type == _VALIDATOR_TYPE_LITERAL:
            if url == self.value:
                return True
        elif self.type == _VALIDATOR_TYPE_REGEX:
            r = _get_targetvalidator_regex(self.value)
            if r.search(url):
                return True
        elif self.type == _VALIDATOR_TYPE_FUNC:
            mname, dot, fname = self.value.rpartition('.')
            # do not catch ImportError here, let it go for debugging purposes
            m = __import__(mname, fromlist=[fname])
            return getattr(m, fname)(url)
        return False

#==============================================================================#
# import models from sub packages

for _pkg in _subpackages:
    __import__(_pkg, fromlist=['models'])

#==============================================================================#











