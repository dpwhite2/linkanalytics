from django.conf.urls.defaults import *# No trailing '/' in FILEPATH, although it may contain '/'.FILEPATH = r'(?P<filepath>(?:(?:/[-\w\d_.])|[-\w\d_.])+)'urlpatterns = patterns('linkanalytics',    (r'^r/'+FILEPATH+r'/?$', 'targetviews.targetview_redirect'),    (r'^h/'+FILEPATH+r'/?$', 'targetviews.targetview_html'),)