from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance #, TrackedUrlTarget, TrackedUrlStats
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm #, TrackedUrlTargetForm

import datetime
import sys
import traceback

from linkanalytics import targeturls


##from linkanalytics.targeturls import urlpatterns

# this should be a configurable setting
_TARGETURLCONF = "linkanalytics.targeturls"


def accessTrackedUrl(request, uuid, tailpath):
    tailpath = '/%s'%tailpath
    qs = TrackedUrlInstance.objects.filter(uuid=uuid)
    if not qs.exists():
        # TODO: error, uuid combination not found
        return HttpResponse('I\'m sorry: I was unable to find that link.')
    
    accessed = qs[0].on_access()
    
    try:
        #viewfunc,args,kwargs = resolve(tailpath, urlconf=_TARGETURLCONF)
        viewfunc,args,kwargs = resolve(tailpath, urlconf=targeturls)
        response = viewfunc(request, uuid, *args, **kwargs)
    #except Resolver404:
    #    # custom 404 message?
    #    accessed.undo()
    #    raise
    except Exception as e:
        # cancel access if an error occurs
        accessed.undo()
        raise
    
    return response


def accessTrackedUrl_old(request, uuid, targetname):
    qs = TrackedUrlInstance.objects.filter(uuid=uuid) #.filter(trackedurl__targets__name=file)
    if not qs.exists():
        # TODO: error, uuid combination not found
        return HttpResponse('I\'m sorry: I was unable to find that link.')
    target = qs[0].on_access(targetname)
    view,arg = target.view_and_arg()
    
    targetviewfunc = getattr(linkanalytics.targetviews, view)
    
    return targetviewfunc(request, uuid, targetname, arg)
    
    #return HttpResponse('Under construction. {0}, {1}'.format(view,arg))
    
    
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













