import re

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404, reverse as urlreverse
from django.core.exceptions import ObjectDoesNotExist


from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm
from linkanalytics import app_settings



# this should be a configurable setting?
_TARGETURLCONF = "linkanalytics.targeturls"

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
    if not tailpath.startswith('/'):
        tailpath = '/%s' % tailpath
    try:
        i = TrackedUrlInstance.objects.get(uuid=uuid)
    except ObjectDoesNotExist:
        raise Http404
    
    if not i.match_hash(hash, tailpath):
        raise Http404
    
    url = request.build_absolute_uri()
    
    try:
        viewfunc, args, kwargs = resolve(tailpath, urlconf=_TARGETURLCONF)
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
        form = TrackedUrlDefaultForm(request.POST, instance=TrackedUrl())
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
        form = TrackeeForm(request.POST, instance=Trackee())
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



