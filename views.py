from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance #, TrackedUrlTarget, TrackedUrlStats
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm #, TrackedUrlTargetForm

import datetime
import sys
import traceback

##from linkanalytics import targeturls


##from linkanalytics.targeturls import urlpatterns

# this should be a configurable setting
_TARGETURLCONF = "linkanalytics.targeturls"


def accessTrackedUrl(request, uuid, tailpath):    
    tailpath = '/%s'%tailpath
    qs = TrackedUrlInstance.objects.filter(uuid=uuid)
    if not qs.exists():
        raise Http404
    
    # TODO: determine url 
    
    try:
        viewfunc,args,kwargs = resolve(tailpath, urlconf=_TARGETURLCONF)
        response = viewfunc(request, uuid, *args, **kwargs)
        # record access only *after* viewfunc() returned
        qs[0].on_access(success=True, url='')
    except Exception as e:
        qs[0].on_access(success=False, url='')
    
    return response
    

def createTrackedUrl(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TrackedUrlDefaultForm(request.POST, instance=TrackedUrl()) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/linkanalytics/create_trackedurl/') # Redirect after POST
    else:
        form = TrackedUrlDefaultForm() # An unbound form

    return render_to_response('linkanalytics/create_trackedurl.html',
                             {'form': form, },
                              context_instance=RequestContext(request))
    
def createTrackee(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TrackeeForm(request.POST, instance=Trackee()) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/linkanalytics/create_trackee/') # Redirect after POST
    else:
        form = TrackeeForm() # An unbound form

    return render_to_response('linkanalytics/create_trackee.html',
                             {'form': form, },
                              context_instance=RequestContext(request))
    
def createTrackedUrlTarget(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TrackedUrlTargetForm(request.POST, instance=Trackee()) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/linkanalytics/create_target/') # Redirect after POST
    else:
        form = TrackedUrlTargetForm() # An unbound form

    return render_to_response('linkanalytics/create_target.html',
                             {'form': form, },
                              context_instance=RequestContext(request))













