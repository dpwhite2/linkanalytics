from django.core.urlresolvers import reverse as urlreverse

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
def hashedurl_redirect_http(trackedurl_instance, domain, filepath=''):
    urltail = urltail_redirect_http(domain, filepath)
    return trackedurl_instance.generate_hashedurl(urltail)
    
def hashedurl_redirect_https(trackedurl_instance, domain, filepath=''):
    urltail = urltail_redirect_https(domain, filepath)
    return trackedurl_instance.generate_hashedurl(urltail)
    
def hashedurl_redirect_local(trackedurl_instance, filepath):
    urltail = urltail_redirect_local(filepath)
    return trackedurl_instance.generate_hashedurl(urltail)
    
def hashedurl_html(trackedurl_instance, filepath):
    urltail = urltail_html(filepath)
    return trackedurl_instance.generate_hashedurl(urltail)
    
def hashedurl_pixelgif(trackedurl_instance):
    urltail = urltail_pixelgif()
    return trackedurl_instance.generate_hashedurl(urltail)
    
def hashedurl_pixelpng(trackedurl_instance):
    urltail = urltail_pixelpng()
    return trackedurl_instance.generate_hashedurl(urltail)

#==============================================================================#
def create_hashedurl(hash, uuid, urltail):
    if not urltail.startswith('/'):
        urltail = '/%s'%urltail
    kwargs = { 'hash': hash, 'uuid': uuid, 'tailpath': urltail }
    return urlreverse('linkanalytics-accesshashedview', kwargs=kwargs)

#==============================================================================#

