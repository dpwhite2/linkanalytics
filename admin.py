from django.contrib import admin

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, TrackedUrlTarget, Trackee, Email

def targets_count(obj):
    return '%d'%obj.targets.count()
targets_count.short_description = 'Targets'
def trackees_count(obj):
    return '%d'%obj.trackees.count()
trackees_count.short_description = 'Trackees'

class TargetsInline(admin.TabularInline):
    model = TrackedUrl.targets.through
class TrackeesInline(admin.TabularInline):
    model = TrackedUrl.trackees.through

class TrackedUrlAdmin(admin.ModelAdmin):
    list_display = ('name', trackees_count, targets_count,)
    inlines = [ TargetsInline, TrackeesInline ]
    
class TrackedUrlTargetAdmin(admin.ModelAdmin):
    list_display = ('name','urltype','path',)
    
class TrackeeAdmin(admin.ModelAdmin):
    list_display = ('username','emailaddress','first_name','last_name','is_django_user',)

admin.site.register(TrackedUrl, TrackedUrlAdmin)
admin.site.register(TrackedUrlInstance)
admin.site.register(TrackedUrlTarget, TrackedUrlTargetAdmin)
admin.site.register(Trackee, TrackeeAdmin)
admin.site.register(Email)












