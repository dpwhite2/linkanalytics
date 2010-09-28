from django.conf import settings

# Do not change the defaults in this file.  To modify the settings for your own 
# deployment, define the setting (with "LINKANALYTICS_" prefix) in your project's 
# settings.py.  

# Settings to add:

# linkanalytics app base url (everything before the '/linkanalytics/...')
# It must NOT include a trailing slash.
URLBASE = settings.LINKANALYTICS_URLBASE
#   ... or get this from HttpRequest, since email has to be composed from a view.  But then that limits auto delivery. hmmm...

# TrackedUrlAccess.url length (default: 3000?)
# Email and DraftEmail: max subject length
# optional custom targeturls module (so user can add his/her own views)
# extra targetviews directory? (so user can non-intrusively override linkanalytics defaults)
# Not configurable by user:
#   for use in email templates: linkid variable name (should just be 'linkid')
#   for use in email templates: urlbase variable name (should just be 'urlbase')

