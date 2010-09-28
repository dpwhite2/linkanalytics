from django.conf.urls.defaults import *

from django.contrib import admin

from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^daveday1/', include('daveday1.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    # The following static file views must only be enabled for the development server.
    #(r'^media/linkanalytics/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/dpwhite2/linkanalytics/linkanalytics/media'}),

    (r'^linkanalytics/', include('linkanalytics.urls')),

)
