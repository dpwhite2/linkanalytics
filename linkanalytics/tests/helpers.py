"""
    Various utilities to aid in writing tests.
"""
from django.core.urlresolvers import reverse as urlreverse

# Disable Nose test autodiscovery for this module.
__test__ = False

#==============================================================================#
def _put_htmldoc_newlines(data):
    """Put newlines into html source where HtmlDocument places them."""
    data = data.replace('<html>','<html>\n')
    data = data.replace('</html>','</html>\n')
    data = data.replace('</head>','</head>\n')
    data = data.replace('</body>','</body>\n')
    return data
    
def urlreverse_redirect_http(uuid, domain, filepath=''):
    urltail = urlreverse('redirect-http', urlconf='linkanalytics.targeturls', kwargs={'domain':domain,'filepath':filepath})
    urltail = urltail[1:] # remove leading '/'
    return urlreverse('linkanalytics-accessview', kwargs={'uuid': uuid, 'tailpath':urltail})
    
def urlreverse_redirect_local(uuid, filepath):
    urltail = urlreverse('redirect-local', urlconf='linkanalytics.targeturls', kwargs={'filepath':filepath})
    urltail = urltail[1:] # remove leading '/'
    return urlreverse('linkanalytics-accessview', kwargs={'uuid': uuid, 'tailpath':urltail})
    
#==============================================================================#

