import hmac

from django.core.urlresolvers import reverse as urlreverse

from linkanalytics import app_settings

#==============================================================================#
def urltail_redirect_http(domain, filepath=''):
    return urlreverse('redirect-http', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_https(domain, filepath=''):
    return urlreverse('redirect-https', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'domain':domain, 'filepath':filepath})
                      
def urltail_redirect_local(filepath):
    return urlreverse('redirect-local', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_html(filepath):
    return urlreverse('targetview-html', urlconf=app_settings.TARGETS_URLCONF, 
                      kwargs={'filepath':filepath})
                      
def urltail_pixelgif():
    return urlreverse('targetview-pixelgif', 
                      urlconf=app_settings.TARGETS_URLCONF)
                      
def urltail_pixelpng():
    return urlreverse('targetview-pixelpng', 
                      urlconf=app_settings.TARGETS_URLCONF)

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
                    app_settings.DIGEST_CTOR).hexdigest()
                    
def create_hashedurl(uuid, urltail):
    if not urltail.startswith('/'):
        urltail = '/%s' % urltail
    hash = generate_urlhash(uuid, urltail)
    return assemble_hashedurl(hash, uuid, urltail[1:])
                    
def assemble_hashedurl(hash, uuid, urltail):
    kwargs = { 'hash': hash, 'uuid': uuid, 'tailpath': urltail }
    return urlreverse('linkanalytics-accesshashedview', kwargs=kwargs)

#==============================================================================#

