import hashlib
import hmac

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics import app_settings

_TARGETURLCONF = "linkanalytics.targeturls"


#==============================================================================#
def urltail_redirect_http(domain, filepath=''):
    return urlreverse('redirect-http', urlconf=_TARGETURLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_https(domain, filepath=''):
    return urlreverse('redirect-https', urlconf=_TARGETURLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_local(filepath):
    return urlreverse('redirect-local', urlconf=_TARGETURLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_html(filepath):
    return urlreverse('targetview-html', urlconf=_TARGETURLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_pixelgif():
    return urlreverse('targetview-pixelgif', urlconf=_TARGETURLCONF)
                      
def urltail_pixelpng():
    return urlreverse('targetview-pixelpng', urlconf=_TARGETURLCONF)

#==============================================================================#
def hashedurl_redirect_http(uuid, domain, filepath=''):
    urltail = urltail_redirect_http(domain, filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_redirect_https(uuid, domain, filepath=''):
    urltail = urltail_redirect_https(domain, filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_redirect_local(uuid, filepath):
    urltail = urltail_redirect_local(filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_html(uuid, filepath):
    urltail = urltail_html(filepath)
    return create_hashedurl(uuid, urltail)
    
def hashedurl_pixelgif(uuid):
    urltail = urltail_pixelgif()
    return create_hashedurl(uuid, urltail)
    
def hashedurl_pixelpng(uuid):
    urltail = urltail_pixelpng()
    return create_hashedurl(uuid, urltail)

#==============================================================================#
def generate_urlhash(uuid, urltail):
    """Generates a hash for the given urltail and uuid.  The return value is a 
       string of hexadecimal digits representing the hash value.
    """
    return hmac.new(app_settings.SECRET_KEY, uuid+urltail, 
                    hashlib.sha1).hexdigest()
                    
def create_hashedurl(uuid, urltail):
    if not urltail.startswith('/'):
        urltail = '/%s' % urltail
    hash = generate_urlhash(uuid, urltail)
    return assemble_hashedurl(hash, uuid, urltail[1:])
                    
def assemble_hashedurl(hash, uuid, urltail):
    #if not urltail.startswith('/'):
    #    urltail = '/%s' % urltail
    kwargs = { 'hash': hash, 'uuid': uuid, 'tailpath': urltail }
    return urlreverse('linkanalytics-accesshashedview', kwargs=kwargs)
    
#def create_hashedurl(hash, uuid, urltail):
#    if not urltail.startswith('/'):
#        urltail = '/%s' % urltail
#    kwargs = { 'hash': hash, 'uuid': uuid, 'tailpath': urltail }
#    return urlreverse('linkanalytics-accesshashedview', kwargs=kwargs)

#==============================================================================#

