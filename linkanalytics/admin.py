from django.contrib import admin

from linkanalytics.models import Tracker, TrackedInstance, Visitor
from linkanalytics.models import Access

import linkanalytics.email.admin  # register email admin classes

def visitors_count(obj):
    return '%d'%obj.visitors.count()
visitors_count.short_description = 'Visitors'


class VisitorsInline(admin.TabularInline):
    model = Tracker.visitors.through

class TrackerAdmin(admin.ModelAdmin):
    list_display = ('name', visitors_count, )
    inlines = [ VisitorsInline ]
    

class VisitorAdmin(admin.ModelAdmin):
    list_display = ('username', 'emailaddress', 'first_name', 'last_name', 
                    'is_django_user', )
    


class AccessInline(admin.TabularInline):
    model = Access

class TrackedInstanceAdmin(admin.ModelAdmin):
    list_display = ('tracker', 'visitor', 'uuid', 'notified', )
    inlines = [ AccessInline, ]
    


admin.site.register(Tracker, TrackerAdmin)
admin.site.register(TrackedInstance, TrackedInstanceAdmin)
admin.site.register(Visitor, VisitorAdmin)












