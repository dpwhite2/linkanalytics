from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance, TrackedUrlTarget, TrackedUrlStats
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm, TrackedUrlTargetForm

import datetime

import linkanalytics.targetviews


def accessTrackedUrl(request, uuid, targetname):
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













