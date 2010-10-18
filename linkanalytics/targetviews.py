import os.path

from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext

from django.template import TemplateDoesNotExist

from linkanalytics import app_settings, decorators


#==============================================================================#
@decorators.targetview()
def targetview_html(request, uuid, filepath=None):
    """Renders a given HTML file."""
    if not filepath:
        filepath = 'default.html'
    return render_to_response('linkanalytics/targetviews/%s'%filepath,
                              context_instance=RequestContext(request))

@decorators.targetview()
def targetview_redirect(request, uuid, scheme=None, domain=None, filepath=None):
    """Redirects to another URL.  Unlike other targetviews, this function uses 
       HttpResponseRedirect.
    
       scheme:      The URI scheme (e.g. http, https).  If not provided, http 
                    is assumed.
       domain:      The URL domain name, including the optional port.
       filepath:    Everything in the URL that follows the domain.
       
       Either domain or filepath (or both) must be provided.  If a domain is 
       not present, the filepath is appended to the default site, and the 
       scheme argument is ignored.
    """
    
    if (not domain) and (not filepath):
        msg = 'Either "domain" or "filepath" (or both) must be provided.'
        raise TypeError(msg)
    
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

@decorators.targetview()
def targetview_pixelgif(request, uuid):
    """Returns a response to a one-pixel transparent GIF image."""
    msg = 'Target view: targetview_pixelgif().  Under Construction'
    return HttpResponse(msg)
    
@decorators.targetview()
def targetview_pixelpng(request, uuid):
    """Returns a response to a one-pixel transparent PNG image."""
    fname = os.path.join(app_settings.PIXEL_IMGDIR,'blank.png')
    with open(fname, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')
        
#==============================================================================#


