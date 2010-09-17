from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.sites.models import Site

from django.template import TemplateDoesNotExist


#def view_unknown(request, uuid, targetname, arg):
#    return HttpResponse('Target view: UNKNOWN.  Under Construction')

#def view_txt(request, uuid, targetname, arg):
#    return HttpResponse('Target view: TXT.  Under Construction')


def targetview_html(request, uuid, filepath=None):
    if not filepath:
        filepath = 'default.html'
    return render_to_response('linkanalytics/targetviews/%s'%filepath,
                              context_instance=RequestContext(request))

def targetview_redirect(request, uuid, scheme=None, domain=None, filepath=None):
    """Redirects to another URL.  Unlike other targetviews, this function uses HttpResponseRedirect.
    
       scheme:      The URI scheme (e.g. http, https).  If not provided, http is assumed.
       domain:      The URL domain name, including the optional port.
       filepath:    Everything in the URL that follows the domain.
       
       Either domain or filepath (or both) must be provided.  If a domain is 
       not present, the filepath is appended to the default site, and the 
       scheme argument is ignored.
    """
    
    if (not domain) and (not filepath):
        raise TypeError('Either "domain" or "filepath" (or both) must be provided.')
    
    if not domain:
        # also ignore scheme
        url = '/{f}'.format(f=filepath)
    else:
        if not scheme:
            scheme = 'http'
        if not filepath:
            filepath = ''
        url = '{s}://{d}/{f}'.format(s=scheme, d=domain, f=filepath)
    
    response = redirect(url)
    return response


