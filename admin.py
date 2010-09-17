from django.contrib import admin

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, Trackee, Email #TrackedUrlTarget, TrackedUrlStats

def trackees_count(obj):
    return '%d'%obj.trackees.count()
trackees_count.short_description = 'Trackees'


class TrackeesInline(admin.TabularInline):
    model = TrackedUrl.trackees.through

class TrackedUrlAdmin(admin.ModelAdmin):
    list_display = ('name', trackees_count, )
    inlines = [ TrackeesInline ]
    

class TrackeeAdmin(admin.ModelAdmin):
    list_display = ('username','emailaddress','first_name','last_name','is_django_user',)
    

class TrackedUrlInstanceAdmin(admin.ModelAdmin):
    list_display = ('trackedurl','trackee','uuid','notified',)
    #inlines = [ TrackedUrlStatsInline, ]

admin.site.register(TrackedUrl, TrackedUrlAdmin)
admin.site.register(TrackedUrlInstance, TrackedUrlInstanceAdmin)
admin.site.register(Trackee, TrackeeAdmin)
admin.site.register(Email)












