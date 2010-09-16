from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext


#def view_unknown(request, uuid, targetname, arg):
#    return HttpResponse('Target view: UNKNOWN.  Under Construction')

#def view_txt(request, uuid, targetname, arg):
#    return HttpResponse('Target view: TXT.  Under Construction')

def targetview_html(request, uuid, filepath=None):
    print 'in targetview_html()'
    if not filepath:
        filepath = 'default.html'
    return render_to_response('linkanalytics/targetviews/%s'%filepath,
                              context_instance=RequestContext(request))



