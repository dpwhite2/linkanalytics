import re

from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist

from linkanalytics.models import Trackee, resolve_emails
from linkanalytics.email.models import Email, DraftEmail

#==============================================================================#
# - Automatically create tracked_urls for the email: an image and a link.
# - Provide ability for link customization
# - allow trackees to be added
# - allow ability to create quick trackees

# Split on commas and/or whitespace
_re_toemailsplit = re.compile(r'[\s,]+')
_re_username = re.compile(r'^[_\w\d]+$')

class ToEmailField(forms.Field):
    def to_python(self, value):
        if not value:
            return []
        return _re_toemailsplit.split(value)
        
    def validate(self, value):
        super(ToEmailField, self).validate(value)
        # a part can either be an email address or a known username
        for part in value:
            if _re_username.match(part):
                try:
                    t = Trackee.objects.get(username=part)
                except ObjectDoesNotExist:
                    msg = 'Recipient {0} was not found.'.format(part)
                    raise forms.ValidationError(msg)
                if t.emailaddress == '':
                    msg = 'Recipient {0} does not have ' + \
                          'an email address.'.format(t.username)
                    raise forms.ValidationError(msg)
            else:
                validate_email(part)


class ComposeEmailForm(forms.ModelForm):
    #to = forms.CharField(widget=forms.Textarea, required=False)
    to = ToEmailField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = DraftEmail
        exclude = ['sent', 'pending_recipients']
        
    def __init__(self, *args, **kwargs):
        super(ComposeEmailForm, self).__init__(*args, **kwargs)
        # populate the initial values of 'to'
        if 'instance' in kwargs:
            recs = ', '.join(r.username for r in 
                             self.instance.pending_recipients.all())
            self.fields['to'].initial = recs
        if self.instance.sent:
            boundfields = self.visible_fields()
            for bf in boundfields:
                bf.field.widget.attrs['disabled'] = 'true'
    
    def save(self, *args, **kwargs):
        # disallow modifications if already sent
        if not self.instance.sent:
            return super(ComposeEmailForm, self).save(*args, **kwargs)
        else:
            return DraftEmail.objects.get(pk=self.instance.pk)
        

class CreateContactForm(forms.ModelForm):
    # Override the default Trackee emailaddress field, which is *not* required.
    emailaddress = forms.EmailField(required=True)
    class Meta:
        model = Trackee
        exclude = ['is_django_user',]
        











