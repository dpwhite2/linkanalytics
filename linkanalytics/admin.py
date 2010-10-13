from django.contrib import admin

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, Trackee
from linkanalytics.models import TrackedUrlAccess

import linkanalytics.email.admin  # register email admin classes

def trackees_count(obj):
    return '%d'%obj.trackees.count()
trackees_count.short_description = 'Trackees'


class TrackeesInline(admin.TabularInline):
    model = TrackedUrl.trackees.through

class TrackedUrlAdmin(admin.ModelAdmin):
    list_display = ('name', trackees_count, )
    inlines = [ TrackeesInline ]
    

class TrackeeAdmin(admin.ModelAdmin):
    list_display = ('username', 'emailaddress', 'first_name', 'last_name', 
                    'is_django_user', )
    


class TrackedUrlAccessInline(admin.TabularInline):
    model = TrackedUrlAccess

class TrackedUrlInstanceAdmin(admin.ModelAdmin):
    list_display = ('trackedurl', 'trackee', 'uuid', 'notified', )
    inlines = [ TrackedUrlAccessInline, ]
    


admin.site.register(TrackedUrl, TrackedUrlAdmin)
admin.site.register(TrackedUrlInstance, TrackedUrlInstanceAdmin)
admin.site.register(Trackee, TrackeeAdmin)












