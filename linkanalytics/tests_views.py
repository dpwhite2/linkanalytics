"""
Some views used only during testing.
"""

# Disable Nose test autodiscovery for this module.
__test__ = False

from django.http import HttpResponse, HttpResponseNotFound

def testview(request):
    html = """<html><body>This is a test page.  So there.</body></html>"""
    return HttpResponse(html)

def on_page_not_found(request):
    html = """<html><body>This is a test 404 page.  So there.</body></html>"""
    response = HttpResponseNotFound(html)
    response['Location'] = 'http://{0}/{1}'.format(request.get_host(), request.path)
    
    return response
    


