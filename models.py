from django.db import models
from django.contrib.auth.models import User
#from django.db.models import F

import uuid
import datetime

# TRACKED_URL_TYPES = (
    # ('P', 'png', 'image/png'),
    # ('G', 'gif', 'image/gif'),
    # ('H', 'html', 'text/html'),
    # ('T', 'txt', 'text/plain'),
    # ('X', 'xml', 'text/xml'),
    # ('V', 'view', ''),
    # ('?', 'unknown', ''),
    # )
    
# _tracked_url_types = dict((x[0],x) for x in TRACKED_URL_TYPES)

# TRACKED_URL_TYPEABBREVS = tuple((a,t) for (a,t,m) in TRACKED_URL_TYPES)

TRACKED_URL_VIEWS = (
    ('P', 'png', 'view_png'),
    ('G', 'gif', 'view_gif'),
    ('H', 'html', 'view_html'),
    ('T', 'txt', 'view_txt'),
    ('X', 'xml', 'view_xml'),
    ('R', 'redirect', 'view_redirect'),
    ('?', 'unknown', 'view_unknown'),
    )
    
_tracked_url_views = dict((x[0],x) for x in TRACKED_URL_VIEWS)

TRACKED_URL_VIEWS_GUILIST = tuple((k,t) for (k,t,v) in TRACKED_URL_VIEWS)

# Length of the first item in TRACKED_URL_TYPES tuples.
TRACKED_URL_TYPEABBREVS_KEY_LENGTH = 1

# Length of the longest item in TRACKED_URL_VIEWS tuples.
TRACKED_URL_VIEWS_KEY_LENGTH = max(len(k) for k in _tracked_url_views)


# Design:
#
# A *TrackedUrl* represents a url whose accesses are tracked.

# Each TrackedUrl is associated with zero or more *TrackedUrlInstances*.  Each of 
# those instances tracks when a single user accesses a single url.  A 
# TrackedUrlInstance is associated with exactly one TrackedUrl and one user.

# Each TrackedUrl is also associated with one or more *TrackedUrlTargets*.  A 
# target represents what is returned when a tracked link is accessed.  There is a 
# many-to-many relationship between the TrackedUrlTarget and TrackedUrl. 

# A *Trackee* is the actor whose url accesses are tracked.  Trackees and 
# TrackedUrls have a many-to-many relationship through the TrackedUrlInstance 
# class.

# Trackees and TrackedUrls are created by the administrator.  
# TrackedUrlInstances are created by the application.  TrackedUrlTargets can be 
# created by the administrator or by the application, and some are provided 
# with the installation.


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
        return TrackedUrlInstance.objects.filter(trackee=self.pk)
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
                        

class TrackedUrlTarget(models.Model):
    name =          models.CharField(max_length=64, unique=True)  # the url part that appears after the uuid
    view =          models.CharField(max_length=TRACKED_URL_VIEWS_KEY_LENGTH, choices=TRACKED_URL_VIEWS_GUILIST)
    arg =           models.CharField(max_length=256, blank=True)
    # Possible built-in Targets: 
    #   1x1 px image, 
    #   generic HTML "Your usage has been counted. Thank you.", 
    #   generic HTML for email links
    
    def __unicode__(self):
        return u'%s'%self.name
        
    def trackedurls(self):
        return TrackedUrl.objects.filter(targets=self.pk)
        
    @staticmethod
    def get_unknown_target():
        qs = TrackedUrlTarget.objects.filter(name='<UNKNOWN>',view='?')
        if not qs.exists():
            t = TrackedUrlTarget(name='<UNKNOWN>',view='?',arg='')
            t.save()
        else:
            t = qs[0]
        return t
        
    def view_and_arg(self):
        k,ty,view = _tracked_url_views[self.view]
        return view,self.arg


class TrackedUrl(models.Model):
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    # Every target,trackee pair must be unique
    targets =   models.ManyToManyField(TrackedUrlTarget, through='UrlTargetPair')
    trackees =  models.ManyToManyField(Trackee, through='TrackedUrlInstance')
    
    def __unicode__(self):
        return u'%s'%self.name
    
    def url_instances(self):
        return TrackedUrlInstance.objects.filter(trackedurl=self.pk)
    def url_instances_read(self):
        # find all instances that have at least one linked TrackedUrlStats with a non-None first_access
        return self.trackedurlinstance_set.annotate(
                    num_accesses=models.Sum('trackedurlstats__access_count')
                ).filter(num_accesses__gt=0)
        
    def add_target(self, target):
        p = UrlTargetPair(trackedurl=self, target=target)
        p.save()
        return p
    def add_trackee(self, trackee):
        i = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        i.save()
        return i


def _create_uuid():
    return uuid.uuid4().hex
        

class TrackedUrlInstance(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    trackee =       models.ForeignKey(Trackee)
    #target =        models.ForeignKey(TrackedUrlTarget)
    uuid =          models.CharField(max_length=32, editable=False, default=_create_uuid, unique=True)
    
    notified =      models.DateField(null=True, blank=True)
    #first_access =  models.DateField(null=True, blank=True)
    #recent_access = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = (("trackedurl", "trackee", ),)
    
    def __unicode__(self):
        return u'%s, %s'%(self.trackedurl, self.trackee)
        
    def targets(self):
        return self.trackedurl.targets.all()
        
    def was_accessed(self):
        return self.access_count() > 0
        
    def recent_access(self):
        d = self.trackedurlstats_set.aggregate(models.Max('recent_access'))
        return d['recent_access__max']
    def first_access(self):
        d = self.trackedurlstats_set.aggregate(models.Min('first_access'))
        return d['first_access__min']
    def access_count(self):
        d = self.trackedurlstats_set.aggregate(models.Sum('access_count'))
        s = d['access_count__sum']
        return s  if s is not None else  0
        
    def on_access(self, targetname):
        tqs = self.trackedurl.targets.filter(name=targetname)
        c = tqs.count()
        if c==1:
            target = tqs[0]
        elif c==0:
            # if the target was not found, use the 'unknown' target
            target = TrackedUrlTarget.get_unknown_target()
        else:
            # this is an error, should only find zero or one matching object
            raise RuntimeError()
        
        qs = TrackedUrlStats.objects.filter(instance=self, target=target)
        c = qs.count()
        if c==1:
            stats = qs[0]
        elif c==0:
            stats = TrackedUrlStats(instance=self, target=target)
            stats.save()
        else:
            # this is an error, should only find zero or one matching object
            raise RuntimeError()
        
        today = datetime.date.today()
        
        stats.access_count = models.F('access_count') + 1
        if not stats.first_access:
            stats.first_access = today
        stats.recent_access = today
        stats.save()
        
        return target
        
        
# This is kept separate from the TrackedUrlInstance class so that instances may be deleted without losing the tracking information.
class TrackedUrlStats(models.Model):
    instance =      models.ForeignKey(TrackedUrlInstance)
    target =        models.ForeignKey(TrackedUrlTarget)
    
    first_access =  models.DateField(null=True, blank=True)
    recent_access = models.DateField(null=True, blank=True)
    access_count =  models.IntegerField(default=0)
    
    class Meta:
        # The combined values of the fields "trackedurl", "trackee" must be unique for each UrlInstance.
        unique_together = (("instance", "target"),)
    
    def __unicode__(self):
        return u'%s (via %s) accessed: %s (first: %s), total: %d' % (
                    self.instance, self.target, 
                    self.first_access.isoformat(), self.recent_access.isoformat(), self.access_count)

        

# The main purpose of this class is to enforce the uniqueness of every ("trackedurl", "target") pair.
class UrlTargetPair(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    target =       models.ForeignKey(TrackedUrlTarget)
    
    class Meta:
        unique_together = (("trackedurl", "target"),)
    
    def __unicode__(self):
        return u'%s, %s'%(self.trackedurl, self.target)
    

#==============================================================================#
# Extras:

class Email(models.Model):
    recipients =    models.ManyToManyField(Trackee)
    fromemail =     models.EmailField()
    sent =          models.BooleanField(default=False)
    trackedurls =   models.ManyToManyField(TrackedUrl)
    message =       models.TextField()
    
















