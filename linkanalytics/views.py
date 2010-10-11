import datetime
import sys
import traceback
import re

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404, reverse as urlreverse
from django.core.exceptions import ObjectDoesNotExist


from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance
from linkanalytics.models import generate_hash
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm
from linkanalytics import app_settings



# this should be a configurable setting?
_TARGETURLCONF = "linkanalytics.targeturls"

#==============================================================================#
def _donothing(tailpath):
    return tailpath
    
def _ttv_http(tailpath):
    # tailpath begins '/http'
    return 'http://'+tailpath[5:]
    
def _ttv_https(tailpath):
    # tailpath begins '/https'
    return 'https://'+tailpath[6:]
    
def _ttv_local(tailpath):
    # tailpath begins '/r' or '/h'
    return tailpath[2:]
    
_target_to_validate_convertors = {
    'http': _ttv_http,
    'https': _ttv_https,
    'h': _ttv_local,
    'r': _ttv_local,
    }
    
# Get the string from the beginning up until the first slash, or if it begins 
# with a slash, up until the second slash.  No slashes are included in the 
# captured substring.
_re_target_to_validate = re.compile(r'^/?(?P<start>[^/\s]+)(?:/.*)?$')

def _get_target_to_validate(tailpath):
    m = _re_target_to_validate.match(tailpath)
    start = m.group('start')  if m else  tailpath
    return _target_to_validate_convertors.get(start,_donothing)(tailpath)

#==============================================================================#
# Linkanalytics basic views

def accessTrackedUrl(request, uuid, tailpath):
    if (not tailpath.startswith('/')):
        tailpath = '/%s'%tailpath
    try:
        i = TrackedUrlInstance.objects.get(uuid=uuid)
    except ObjectDoesNotExist:
        raise Http404
    
    target_to_validate = _get_target_to_validate(tailpath)
    if not i.validate_target(target_to_validate):
        raise Http404
    
    url = request.build_absolute_uri()
    
    try:
        viewfunc,args,kwargs = resolve(tailpath, urlconf=_TARGETURLCONF)
        response = viewfunc(request, uuid, *args, **kwargs)
        # record access only *after* viewfunc() returned
        i.on_access(success=True, url=url)
    except Exception as e:
        i.on_access(success=False, url=url)
        raise
    
    return response
    
def accessHashedTrackedUrl(request, hash, uuid, tailpath):
    if (not tailpath.startswith('/')):
        tailpath = '/%s'%tailpath
    try:
        i = TrackedUrlInstance.objects.get(uuid=uuid)
    except ObjectDoesNotExist:
        raise Http404
    
    newhash = generate_hash(tailpath)
    if hash != newhash:
        raise Http404
    
    url = request.build_absolute_uri()
    
    try:
        viewfunc,args,kwargs = resolve(tailpath, urlconf=_TARGETURLCONF)
        response = viewfunc(request, uuid, *args, **kwargs)
        # record access only *after* viewfunc() returned
        i.on_access(success=True, url=url)
    except Exception as e:
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



