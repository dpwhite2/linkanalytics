from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import Visitor, resolve_emails
from linkanalytics.email.models import Email, DraftEmail
from linkanalytics.email.forms import ComposeEmailForm, CreateContactForm

#==============================================================================#
# Utility functions

def _email_render_to_response(template, dictionary, context_instance):
    """Helper that adds context variables needed by all email views."""

    sent_count =    Email.objects.all().count()
    draft_count =   DraftEmail.objects.filter(sent=False).count()
    contact_count = Visitor.objects.exclude(emailaddress='').count()
    dictionary.update( {'sent_count': sent_count,
                        'draft_count': draft_count,
                        'contact_count': contact_count} )
    return render_to_response(template, dictionary,
                              context_instance=context_instance)


#==============================================================================#
# Linkanalytics Email views

@login_required
def viewEmail(request):
    """The main view for the Linkanalytics.Email app."""
    return _email_render_to_response('linkanalytics/email/email.html', {},
                              context_instance=RequestContext(request))


@login_required
def composeEmail(request, emailid=None):
    """The view in which to compose an email, or edit an existing (but
       not-yet-sent) email.  If emailid is None, compose a new email; if
       emailid refers to a valid but unsent email, edit the existing email; if
       emailid refers to a valid but sent email, display the contents but do
       not allow it to be edited.
    """
    # TODO: if emailid is not None and not found, do what?
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
    contacts = Visitor.objects.exclude(emailaddress='')
    return _email_render_to_response('linkanalytics/email/compose.html',
                             {'form': form, 'emailid': emailid,
                              'contacts': contacts},
                             context_instance=RequestContext(request))


@login_required
def viewSentEmails(request):
    """The view which displays a list of all sent emails."""
    return _email_render_to_response('linkanalytics/email/sent.html',
                             {'emails': Email.objects.all() },
                              context_instance=RequestContext(request))

@login_required
def viewDraftEmails(request):
    """The view which displays a list of all unsent draft emails."""
    return _email_render_to_response('linkanalytics/email/drafts.html',
                             {'drafts': DraftEmail.objects.filter(sent=False) },
                              context_instance=RequestContext(request))

@login_required
def viewEmailContacts(request):
    """The view which displays a list of all contacts."""
    return _email_render_to_response('linkanalytics/email/contacts.html',
                    { 'contacts': Visitor.objects.exclude(emailaddress='') },
                    context_instance=RequestContext(request))

@login_required
def editEmailHeadersFooters(request):
    """The view through which one may edit headers and footers."""
    # From this view, select a header or footer to edit, or choose to create 
    # a new header or footer.  Another view allows one to do the actual 
    # editing.
    return HttpResponse('View: Under Construction.')

@login_required
def createEmailContact(request, username=None):
    """The view in which one may create and/or edit a contact."""
    if request.method == 'POST': # If the form has been submitted...
        if username is not None:
            t = Visitor.objects.get(username=username)
            if not t.emailaddress:
                return HttpResponse('Contacts must have an email address.')
        else:
            t = Visitor()
        form = CreateContactForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            url = urlreverse('linkanalytics-email-viewcontacts')
            return HttpResponseRedirect(url)
    else:
        if username is not None:
            t = Visitor.objects.get(username=username)
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
    # TODO: if emailid is not found, do what?
    return HttpResponse('View: Under Construction.')


class EmailReadIter(object):
    """Iterate through the read UrlInstances associated with the given email."""
    def __init__(self, email):
        self.tracker = email.tracker
    def __iter__(self):
        for instance in self.tracker.instances_read():
            yield { 'instance': instance,
                    'visitor': instance.visitor,
                  }

@login_required
def viewEmailReadList(request, emailid):
    """The view which displays a list of recipients who have read the given
       email."""
    # TODO: if emailid is not found, do what?
    eml = Email.objects.get(pk=int(emailid))

    itemiter = EmailReadIter(eml)
    return _email_render_to_response('linkanalytics/email/whoread.html',
                             {'email': eml, 'items': itemiter },
                              context_instance=RequestContext(request))


class EmailUnreadIter(object):
    """Iterate through the unread UrlInstances associated with the given
       email."""
    def __init__(self, email):
        self.tracker = email.tracker
    def __iter__(self):
        for instance in self.tracker.instances_unread():
            yield { 'instance': instance,
                    'visitor': instance.visitor,
                  }

@login_required
def viewEmailUnreadList(request, emailid):
    """The view which displays a list of recipients who have not read the given
       email."""
    # TODO: if emailid is not found, do what?
    eml = Email.objects.get(pk=emailid)

    itemiter = EmailUnreadIter(eml)
    return _email_render_to_response('linkanalytics/email/whounread.html',
                             {'email': eml, 'items': itemiter },
                              context_instance=RequestContext(request))


class EmailRecipientIter(object):
    """Iterate through the unread UrlInstances associated with the given
       email."""
    def __init__(self, email):
        self.tracker = email.tracker
    def __iter__(self):
        for instance in self.tracker.instances():
            yield { 'instance': instance,
                    'visitor': instance.visitor,
                  }

@login_required
def viewEmailRecipientsList(request, emailid):
    """The view which displays a list of all recipients who have been sent the
       given email."""
    # TODO: if emailid is not found, do what?
    eml = Email.objects.get(pk=emailid)

    itemiter = EmailRecipientIter(eml)
    return _email_render_to_response('linkanalytics/email/recipients.html',
                             {'email': eml, 'items': itemiter },
                              context_instance=RequestContext(request))

@login_required
def viewSentEmailContent(request, emailid):
    # TODO: if emailid is not found, do what?
    eml = Email.objects.get(pk=emailid)
    content = eml.render(uuid='0'*32)
    return _email_render_to_response('linkanalytics/email/content_sent.html',
                             {'email': eml, 'content': content },
                              context_instance=RequestContext(request))


#==============================================================================#