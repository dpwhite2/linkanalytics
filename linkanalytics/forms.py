import re

from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ObjectDoesNotExist

from linkanalytics.models import Tracker, Visitor, TrackedInstance

#==============================================================================#
class TrackedUrlDefaultForm(forms.ModelForm):
    # - allow trackees to be added
    # - allow targets to be added or created
    # - create quick trackee from an email address 
    #       (but first check if email is present on an existing trackee)
    class Meta:
        model = Tracker
        
#==============================================================================#
class TrackeeForm(forms.ModelForm):
    class Meta:
        model = Visitor
        exclude = ['is_django_user',]

#==============================================================================#









