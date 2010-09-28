from django import forms
from linkanalytics.models import TrackedUrl, Trackee, TrackedUrlInstance, Email, DraftEmail #TrackedUrlTarget

#==============================================================================#
class TrackedUrlDefaultForm(forms.ModelForm):
    # - link Trackees and targets... for each target, create a tracked url instance for each user
    # - allow trackees to be added
    # - allow targets to be added or created
    # - create quick trackee from an email address (but first check if email is present on an existing trackee)
    class Meta:
        model = TrackedUrl
        
        
        
##class TrackedUrlForm(forms.Form):
##    name = forms.CharField()
##    comments = forms.CharField(widget=forms.Textarea)
##    #job = forms.ModelChoiceField() # empty queryset, overridden in ctor   

#==============================================================================#
class TrackeeForm(forms.ModelForm):
    class Meta:
        model = Trackee
        exclude = ['is_django_user',]

#==============================================================================#
#class TrackedUrlTargetForm(forms.ModelForm):
#    class Meta:
#        model = TrackedUrlTarget

# - Automatically create tracked_urls for the email: an image and a link.
# - Provide ability for link customization
# - allow trackees to be added
# - allow ability to create quick trackees
class ComposeEmailForm(forms.ModelForm):
    class Meta:
        model = DraftEmail
        exclude = ['sent',] #'pending_recipients']
    def __init__(self, *args, **kwargs):
        super(ComposeEmailForm,self).__init__(*args,**kwargs)
        if self.instance.sent:
            boundfields = self.visible_fields()
            for bf in boundfields:
                bf.field.widget.attrs['disabled'] = 'true'
    def save(self, *args, **kwargs):
        # disallow modifications if already sent
        if not self.instance.sent:
            return super(ComposeEmailForm,self).save(*args,**kwargs)
        else:
            return DraftEmail.objects.get(pk=self.instance.pk)
        
    











