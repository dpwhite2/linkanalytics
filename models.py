from django.db import models
from django.contrib.auth.models import User

import uuid


TRACKED_URL_TYPES = (
    ('P', 'png'),
    ('G', 'gif'),
    ('H', 'html'),
    ('T', 'txt'),
    ('X', 'xml'),
    ('V', 'view'),
    )
# Length of the first item in TRACKED_URL_TYPES tuples.
TRACKED_URL_TYPES_KEY_LENGTH = 1


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


class TrackedUrl(models.Model):
    name =      models.CharField(max_length=256)
    comments =  models.TextField(blank=True)
    # Every target,trackee pair must be unique
    targets =   models.ManyToManyField('TrackedUrlTarget', through='UrlTargetPair')
    trackees =  models.ManyToManyField(Trackee, through='TrackedUrlInstance')
    
    def __unicode__(self):
        return u'%s'%self.name
    
    def url_instances(self):
        return TrackedUrlInstance.objects.filter(trackedurl=self.pk)
    def url_instances_read(self):
        return TrackedUrlInstance.objects.filter(trackedurl=self.pk).exclude(first_access__isnull=True)
        
    def add_target(self, target):
        p = UrlTargetPair(trackedurl=self, target=target)
        p.save()
        return p
    def add_trackee(self, trackee):
        t = TrackedUrlInstance(trackedurl=self, trackee=trackee)
        t.save()
        return t


def _create_uuid():
    return uuid.uuid4().hex
        

class TrackedUrlInstance(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    trackee =       models.ForeignKey(Trackee)
    uuid =          models.CharField(max_length=32, editable=False, default=_create_uuid, unique=True)
    
    notified =      models.DateField(null=True, blank=True)
    first_access =  models.DateField(null=True, blank=True)
    recent_access = models.DateField(null=True, blank=True)
    
    class Meta:
        # The combined values of the fields "trackedurl" and "trackee" must be unique for each UrlInstance.
        unique_together = (("trackedurl", "trackee"),)
    
    def __unicode__(self):
        return u'%s, %s'%(self.trackedurl, self.trackee)
        
    def was_accessed(self):
        return self.first_access is not None
    def targets(self):
        return TrackedUrlTarget.objects.filter(trackedurl=self.pk)


class TrackedUrlTarget(models.Model):
    name =          models.CharField(max_length=64)  # the url part that appears after the uuid
    urltype =       models.CharField(max_length=TRACKED_URL_TYPES_KEY_LENGTH, choices=TRACKED_URL_TYPES)
    path =          models.CharField(max_length=256)
    # Possible built-in Targets: 
    #   1x1 px image, 
    #   generic HTML "Your usage has been counted. Thank you.", 
    #   generic HTML for email links
    
    def __unicode__(self):
        return u'%s'%self.name
        
    def trackedurls(self):
        return TrackedUrl.objects.filter(targets=self.pk)
        

# The main purpose of this class is to enforce the uniqueness of every ("trackedurl", "target") pair.
class UrlTargetPair(models.Model):
    trackedurl =    models.ForeignKey(TrackedUrl)
    target =       models.ForeignKey(TrackedUrlTarget)
    
    def __unicode__(self):
        return u'%s, %s'%(self.trackedurl, self.target)
    
    class Meta:
        unique_together = (("trackedurl", "target"),)
    

# Extras:

class Email(models.Model):
    recipients =    models.ManyToManyField(Trackee)
    fromemail =     models.EmailField()
    sent =          models.BooleanField(default=False)
    trackedurls =   models.ManyToManyField(TrackedUrl)
    message =       models.TextField()
    



