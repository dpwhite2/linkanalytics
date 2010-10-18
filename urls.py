from django.conf.urls.defaults import *


from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from linkanalytics.urlsaccess import urltuple

urlpatterns = patterns('',
    # Example:
    # (r'^daveday1/', include('daveday1.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    urltuple,
    
    (r'^linkanalytics/', include('linkanalytics.urls')),

)
