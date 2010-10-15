from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext

from linkanalytics.models import TrackedInstance
from linkanalytics.email.models import Email

from linkanalytics import app_settings

#==============================================================================#
def targetview_renderemail(request, uuid):
    """Renders an email for a user. """
    # TODO: What to do if uuid is not found?  (This should not happen because 
    # the uuid needed to be resolved to get here in the first place.)
    i = TrackedInstance.objects.get(uuid=uuid)
    eml = Email.objects.get(tracker=i.tracker)
    content = eml.render(uuid)
    return render_to_response('linkanalytics/email/render_email.html',
                             { 'content': content },
                              context_instance=RequestContext(request))
    
def targetview_acknowledge(request, uuid):
    """A thank you to contacts who acknowledge they received an email."""
    msg = 'Email target view: targetview_acknowledge().  Under Construction'
    return HttpResponse(msg)

#==============================================================================#
