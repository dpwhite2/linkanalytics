import os.path

from django.conf import settings

# Do not change the defaults in this file.  To modify the settings for your own 
# deployment, define the setting (with "LINKANALYTICS_" prefix) in your 
# project's settings.py.  

# Settings to add:

# linkanalytics app base url (everything before the '/linkanalytics/...')
# It must NOT include a trailing slash.
URLBASE = settings.LINKANALYTICS_URLBASE
#   ... or get this from HttpRequest, since email has to be composed from a 
#       view.  But then that limits auto delivery. hmmm...

PIXEL_IMGDIR = getattr(settings, 'LINKANALYTICS_PIXEL_IMGDIR', 
                                 'linkanalytics/media')

# TrackedUrlAccess.url length (default: 3000?)
# Email and DraftEmail: max subject length
# optional custom targeturls module (so user can add his/her own views)
# extra targetviews directory? (so user can non-intrusively override 
#                               linkanalytics defaults)
# Not configurable by user:
#   for use in email templates: linkid variable name (should just be 'linkid')
#   for use in email templates: urlbase variable name (should just be 'urlbase')


# Assumes that this module is in the linkanalytics app directory, and that its 
# __file__ attribute will be an absolute path or a path relative to the current 
# working directory.  If none of these conditions are met, one should set the 
# LINKANALYTICS_ABSPATHBASE setting appropriately.  Theoretically, you should 
# not need to do this unless this module is moved, or unless the working 
# directory is changed between starting Django and this module being loaded.
_DEFAULT_BASEPATH = os.path.dirname(os.path.abspath(__file__))

# Absolute path to the linkanalytics app.  
ABSPATHBASE = getattr(settings, 'LINKANALYTICS_ABSPATHBASE', _DEFAULT_BASEPATH)

EMAIL_HEADERSDIR = getattr(settings, 'LINKANALYTICS_EMAIL_HEADERSDIR', 
        os.path.join(ABSPATHBASE,'templates','linkanalytics','email','headers')
    )
EMAIL_FOOTERSDIR = getattr(settings, 'LINKANALYTICS_EMAIL_FOOTERSDIR', 
        os.path.join(ABSPATHBASE,'templates','linkanalytics','email','footers')
    )


SECRET_KEY = getattr(settings, 'LINKANALYTICS_SECRET_KEY', settings.SECRET_KEY)
