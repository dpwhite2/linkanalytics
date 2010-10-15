import re

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404, reverse as urlreverse
from django.core.exceptions import ObjectDoesNotExist


from linkanalytics.models import Visitor, Tracker, TrackedInstance
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm
from linkanalytics import app_settings

#==============================================================================#
# Linkanalytics basic views
    
def accessHashedTrackedUrl(request, hash, uuid, tailpath):
    """The main view function for all tracking behavior.  
    
       Urls to be tracked are first dispatched here.  If it validates 
       successfully, it is sent on to a 'targetview' which can do almost 
       anything a normal view can do.  On successful return from the 
       targetview, the access is counted and a response is returned.  If 
       targetview raises an exception, the unsuccessful access is noted and the 
       exception is reraised.
    """
    # Implementation note: The access attempt must always be recorded.
    
    url = request.build_absolute_uri()
    if not tailpath.startswith('/'):
        tailpath = '/%s' % tailpath
    # Retrieve the TrackedInstance.
    try:
        i = TrackedInstance.objects.get(uuid=uuid)
    except ObjectDoesNotExist:
        # record failed access in special TrackedInstance
        TrackedInstance.unknown().on_access(success=False, url=url)
        raise Http404
    
    # Validate the URL against the hash value.
    if not i.match_hash(hash, tailpath):
        i.on_access(success=False, url=url)
        raise Http404
    
    # Call the targetview function.
    try:
        viewfunc, args, kwargs = resolve(tailpath, 
                                         urlconf=app_settings.TARGETS_URLCONF)
        response = viewfunc(request, uuid, *args, **kwargs)
        # record access only *after* viewfunc() returned
        i.on_access(success=True, url=url)
    except Exception:
        i.on_access(success=False, url=url)
        raise
    
    return response
    
@login_required
def createTrackedUrl(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TrackedUrlDefaultForm(request.POST, instance=Tracker())
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/linkanalytics/create_trackedurl/')
    else:
        form = TrackedUrlDefaultForm() # An unbound form

    return render_to_response('linkanalytics/create_trackedurl.html',
                             {'form': form, },
                              context_instance=RequestContext(request))
        
@login_required
def createTrackee(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TrackeeForm(request.POST, instance=Visitor())
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/linkanalytics/create_trackee/')
    else:
        form = TrackeeForm() # An unbound form

    return render_to_response('linkanalytics/create_trackee.html',
                             {'form': form, },
                              context_instance=RequestContext(request))

#==============================================================================#



