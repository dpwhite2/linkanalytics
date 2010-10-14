from django.contrib import admin

from linkanalytics.email.models import Email, DraftEmail


class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'tracker', 'htmlmsg_brief', )
    
class DraftEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'message_brief', 'sent', 'pixelimage', 
                    'htmlheader', 'htmlfooter', 'textheader', 'textfooter')

admin.site.register(Email, EmailAdmin)
admin.site.register(DraftEmail, DraftEmailAdmin)












