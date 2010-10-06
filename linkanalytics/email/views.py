from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, Resolver404, reverse as urlreverse

from linkanalytics.models import Trackee, resolve_emails
from linkanalytics.email.models import Email, DraftEmail
from linkanalytics.email.forms import ComposeEmailForm, CreateContactForm

#==============================================================================#
# Utility functions

def _email_render_to_response(template, dictionary, context_instance):
    """Helper that adds context variables needed by all email views."""
    
    sent_count = Email.objects.all().count()
    draft_count = DraftEmail.objects.filter(sent=False).count()
    contact_count = Trackee.objects.exclude(emailaddress='').count()
    dictionary.update( {'sent_count': sent_count, 
                        'draft_count': draft_count, 
                        'contact_count': contact_count} )
    return render_to_response(template, dictionary, 
                              context_instance=context_instance)


#==============================================================================#
# Linkanalytics Email views
    
@login_required
def viewEmail(request):
    return _email_render_to_response('linkanalytics/email/email.html', {},
                              context_instance=RequestContext(request))
    
        
@login_required
def composeEmail(request, emailid=None):
    if request.method == 'POST': # If the form has been submitted...
        if emailid is not None: 
            instance = DraftEmail.objects.get(pk=emailid)
        else:
            instance = DraftEmail()
            instance.save()
        form = ComposeEmailForm(request.POST, instance=instance)
        if form.is_valid(): # All validation rules pass
            # get data in 'to' and convert it to 'trackees'
            d = resolve_emails(form.cleaned_data['to'])
            # Process the data in form.cleaned_data
            draft = form.save(commit=False)
            draft.pending_recipients.clear()
            for t in d['trackees']:
                draft.pending_recipients.add(t)
            draft.save()
            form.save_m2m()
            if 'do_save' in request.POST:
                url = urlreverse('linkanalytics-email-idcompose', 
                                 kwargs={'emailid':draft.pk})
                return HttpResponseRedirect(url)
            elif 'do_send' in request.POST:
                draft.send()
                url = urlreverse('linkanalytics-email-idcompose', 
                                 kwargs={'emailid':draft.pk})
                return HttpResponseRedirect(url)
    else:
        if emailid is not None:
            form = ComposeEmailForm(instance=DraftEmail.objects.get(pk=emailid))
        else:
            form = ComposeEmailForm()
    contacts = Trackee.objects.exclude(emailaddress='')
    return _email_render_to_response('linkanalytics/email/compose.html',
                             {'form': form, 'emailid': emailid, 
                              'contacts': contacts},
                             context_instance=RequestContext(request))

    
@login_required
def viewSentEmails(request):
    return _email_render_to_response('linkanalytics/email/sent.html',
                             {'emails': Email.objects.all() },
                              context_instance=RequestContext(request))
    
@login_required
def viewDraftEmails(request):
    return _email_render_to_response('linkanalytics/email/drafts.html',
                             {'drafts': DraftEmail.objects.filter(sent=False) },
                              context_instance=RequestContext(request))
    
@login_required
def viewEmailContacts(request):
    return _email_render_to_response('linkanalytics/email/contacts.html',
                    { 'contacts': Trackee.objects.exclude(emailaddress='') },
                    context_instance=RequestContext(request))
    
@login_required
def createEmailContact(request, username=None):
    if request.method == 'POST': # If the form has been submitted...
        if username is not None:
            t = Trackee.objects.get(username=username)
            if not t.emailaddress:
                return HttpResponse('Contacts must have an email address.') 
        else:
            t = Trackee()
        form = CreateContactForm(request.POST, instance=t)
        if form.is_valid(): 
            form.save()
            url = urlreverse('linkanalytics-email-viewcontacts')
            return HttpResponseRedirect(url)
    else:
        if username is not None:
            t = Trackee.objects.get(username=username)
            if not t.emailaddress:
                return HttpResponse('Contacts must have an email address.') 
            form = CreateContactForm(instance=t)
        else:
            form = CreateContactForm()
    
    return _email_render_to_response('linkanalytics/email/create_contact.html',
                    { 'form': form },
                    context_instance=RequestContext(request))

    
@login_required
def viewSingleSentEmail(request, emailid):
    return HttpResponse('View: Under Construction.')
        
@login_required
def viewEmailReadList(request, emailid):
    eml = Email.objects.get(pk=emailid)
    u = eml.trackedurl
    
    def items():
        for instance in u.url_instances_read():
            yield { 'urlinstance': instance,
                    'trackee': instance.trackee,
                  }
    
    itemiter = items()
    
    return _email_render_to_response('linkanalytics/email/whoread.html',
                             {'email': eml, 'items': itemiter },
                              context_instance=RequestContext(request))
        
@login_required
def viewEmailUnreadList(request, emailid):
    eml = Email.objects.get(pk=emailid)
    u = eml.trackedurl
    
    def items():
        for instance in u.url_instances_unread():
            yield { 'urlinstance': instance,
                    'trackee': instance.trackee,
                  }
    
    itemiter = items()
    
    return _email_render_to_response('linkanalytics/email/whounread.html',
                             {'email': eml, 'items': itemiter },
                              context_instance=RequestContext(request))
        
@login_required
def viewEmailRecipientsList(request, emailid):
    return HttpResponse('View: Under Construction.')
        
@login_required
def viewSentEmailContent(request, emailid):
    return HttpResponse('View: Under Construction.')

#==============================================================================#