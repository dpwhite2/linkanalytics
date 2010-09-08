from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance, TrackedUrlTarget
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm, TrackedUrlTargetForm

import datetime


def accessTrackedUrl(request, uuid, file):
    qs = TrackedUrlInstance.objects.filter(uuid=uuid).filter(trackedurl__targets__name=file)
    if not qs.exists():
        # TODO: error, uuid/file combination not found
        return HttpResponse('I\'m sorry: I was unable to find that link.')
    if not qs.count()==1:
        # TODO: error, more than one matching url_instance found
        return HttpResponse('Internal error: The link is not unique.')
    inst = qs[0]
    if inst.first_access is None:
        inst.first_access = datetime.date.today()
    inst.recent_access = datetime.date.today()
    
    return HttpResponse('Under construction.')
    
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













