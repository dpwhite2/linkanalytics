from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext


def view_unknown(request, uuid, targetname, arg):
    return HttpResponse('Target view: UNKNOWN.  Under Construction')

def view_txt(request, uuid, targetname, arg):
    return HttpResponse('Target view: TXT.  Under Construction')

def view_html(request, uuid, targetname, arg):
    if not arg:
        arg = 'default.html'
    return render_to_response('linkanalytics/targetviews/%s'%arg,
                              context_instance=RequestContext(request))



