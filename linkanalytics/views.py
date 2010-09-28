from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404

from linkanalytics.models import Trackee, TrackedUrl, TrackedUrlInstance, Email, DraftEmail #, TrackedUrlTarget, TrackedUrlStats
from linkanalytics.forms import TrackedUrlDefaultForm, TrackeeForm, ComposeEmailForm #, TrackedUrlTargetForm

import datetime
import sys
import traceback

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


def composeEmail(request, emailid=None):
    if request.method == 'POST': # If the form has been submitted...
        if emailid is not None: 
            instance = DraftEmail.objects.get(pk=emailid)
        else:
            instance = DraftEmail()
        form = ComposeEmailForm(request.POST, instance=instance) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            draft = form.save()
            if 'do_save' in request.POST:
                return HttpResponseRedirect('/linkanalytics/compose_email/{0}/'.format(draft.pk)) # Redirect after POST
            elif 'do_send' in request.POST:
                # TODO: create Email from DraftEmail, and send it
                draft.send()
                return HttpResponseRedirect('/linkanalytics/compose_email/{0}/'.format(draft.pk)) # Redirect after POST
    else:
        if emailid is not None:
            form = ComposeEmailForm(instance=DraftEmail.objects.get(pk=emailid))
        else:
            form = ComposeEmailForm()

    return render_to_response('linkanalytics/compose_email.html',
                             {'form': form, 'emailid': emailid},
                              context_instance=RequestContext(request))










