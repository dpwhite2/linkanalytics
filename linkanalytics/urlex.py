"""
    Functions for calculating tracked URLs and generating hashed URLs.
"""

import hmac

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics import app_settings

#==============================================================================#
# Basic structure of a Linkanalytics URL:
#   <URLBASE>/linkanalytics/access/j/<HASH>/<UUID>/<URLTAIL>
#
# The functions in this module create and/or process URLs beginning with the 
# '/linkanalytics' portion.  The <URLBASE> part is dealt with elsewhere.
#
# The <HASH> is used to validate that a URL was created by Linkanalytics.
# The <UUID> determines who is visiting a URL and which Tracker is being 
# visited.
# The <URLTAIL> is redirected to the appropriate targetview via a targeturl 
# conf.  It may contain forward slashes--everything after the UUID is the 
# <URLTAIL>.
#
# The '/linkanalytics/access/j' portion is just the default.  If the urlconf is 
# customized, this portion of the URL may be different.
#==============================================================================#

#==============================================================================#
# Create the 'tail' portion of a tracked URL.

def urltail_redirect_http(domain, filepath=''):
    """Create a urltail that will redirect to an arbitrary http:// URL."""
    return urlreverse('redirect-http', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_https(domain, filepath=''):
    """Create a urltail that will redirect to an arbitrary https:// URL."""
    return urlreverse('redirect-https', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_local(filepath):
    """Create a urltail that will redirect to an arbitrary local url."""
    return urlreverse('redirect-local', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_html(filepath):
    """Create a urltail that will forward to an arbitrary local html page."""
    return urlreverse('targetview-html', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_pixelgif():
    """Create a urltail that will forward to the gif pixel image."""
    return urlreverse('targetview-pixelgif', 
                      urlconf=app_settings.TARGETS_URLCONF)
                      
def urltail_pixelpng():
    """Create a urltail that will forward to the png pixel image."""
    return urlreverse('targetview-pixelpng', 
                      urlconf=app_settings.TARGETS_URLCONF)

#==============================================================================#
def hashedurl_redirect_http(uuid, domain, filepath=''):
    """Create a hashed Linkanalytics URL that will redirect to an arbitrary 
       http:// URL."""
    urltail = urltail_redirect_http(domain, filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_redirect_https(uuid, domain, filepath=''):
    """Create a hashed Linkanalytics URL that will redirect to an arbitrary 
       https:// URL."""
    urltail = urltail_redirect_https(domain, filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_redirect_local(uuid, filepath):
    """Create a hashed Linkanalytics URL that will redirect to an arbitrary 
       local URL."""
    urltail = urltail_redirect_local(filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_html(uuid, filepath):
    """Create a hashed Linkanalytics URL that will forward to an arbitrary 
       local html page."""
    urltail = urltail_html(filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_pixelgif(uuid):
    """Create a hashed Linkanalytics URL that will forward to the gif pixel 
       image."""
    urltail = urltail_pixelgif()
    return create_hashedurl(uuid, urltail)
    
def hashedurl_pixelpng(uuid):
    """Create a hashed Linkanalytics URL that will forward to the png pixel 
       image."""
    urltail = urltail_pixelpng()
    return create_hashedurl(uuid, urltail)

#==============================================================================#
def generate_urlhash(uuid, urltail):
    """Generates a hash for the given urltail and uuid.  The return value is a 
       string of hexadecimal digits representing the hash value.
    """
    return hmac.new(app_settings.SECRET_KEY, uuid+urltail, 
                    app_settings.DIGEST_CTOR).hexdigest()
                    
def create_hashedurl(uuid, urltail):
    """Create a hashed Linkanalytics URL from the given uuid and urltail."""
    if not urltail.startswith('/'):
        urltail = '/%s' % urltail
    hash = generate_urlhash(uuid, urltail)
    return assemble_hashedurl(hash, uuid, urltail[1:])
                    
def assemble_hashedurl(hash, uuid, urltail):
    """Assemble a hashed URL from its components.  The hash must be calculated 
       *before* calling this function."""
    kwargs = { 'hash': hash, 'uuid': uuid, 'tailpath': urltail }
    return urlreverse('linkanalytics-accesshashedview', kwargs=kwargs)

#==============================================================================#

