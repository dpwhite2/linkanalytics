from django.contrib import admin

from linkanalytics.models import TrackedUrl, TrackedUrlInstance, Trackee, TrackedUrlAccess
from linkanalytics.models import Email, DraftEmail

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
    


class TrackedUrlAccessInline(admin.TabularInline):
    model = TrackedUrlAccess

class TrackedUrlInstanceAdmin(admin.ModelAdmin):
    list_display = ('trackedurl','trackee','uuid','notified',)
    inlines = [ TrackedUrlAccessInline, ]
    
class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject','trackedurl','htmlmsg_brief',)
    
class DraftEmailAdmin(admin.ModelAdmin):
    list_display = ('subject','message_brief','sent','pixelimage','htmlheader','htmlfooter','textheader','textfooter')

admin.site.register(TrackedUrl, TrackedUrlAdmin)
admin.site.register(TrackedUrlInstance, TrackedUrlInstanceAdmin)
admin.site.register(Trackee, TrackeeAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(DraftEmail, DraftEmailAdmin)












