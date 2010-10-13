import os.path

from django.conf import settings

# Do not change the defaults in this file.  To modify the settings for your own
# deployment, define the setting (with "LINKANALYTICS_" prefix) in your
# project's settings.py.

def getsettings(name, default):
    """Wrapper around the builtin getattr() which returns the value from 
       settings.LINKANALYTICS_<name>."""
    return getattr(settings, 'LINKANALYTICS_{0}'.format(name), default)

# Settings to add:

# linkanalytics app base url (everything before the '/linkanalytics/...')
# It must NOT include a trailing slash.
URLBASE = settings.LINKANALYTICS_URLBASE
#   ... or get this from HttpRequest, since email has to be composed from a
#       view.  But then that limits auto delivery. hmmm...

# Where to find the pixel images.  The default is the media subdirectory.
PIXEL_IMGDIR = getsettings('PIXEL_IMGDIR', 'linkanalytics/media')

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
ABSPATHBASE = getsettings('ABSPATHBASE', _DEFAULT_BASEPATH)

_EMAIL_TEMPLATESDIR = os.path.join('templates','linkanalytics','email')

EMAIL_HEADERSDIR = getsettings('EMAIL_HEADERSDIR', 
                    os.path.join(ABSPATHBASE, _EMAIL_TEMPLATESDIR, 'headers'))
EMAIL_FOOTERSDIR = getsettings('EMAIL_FOOTERSDIR', 
                    os.path.join(ABSPATHBASE, _EMAIL_TEMPLATESDIR, 'footers'))

# Secret key used in hashing URLs.  If LINKANALYTICS_SECRET_KEY is not found or
# evaluates to False, the SECRET_KEY provided in settings.py is used.
SECRET_KEY = getsettings('SECRET_KEY', '')
if not SECRET_KEY:
    SECRET_KEY = settings.SECRET_KEY

# Location of the urlconf used to redirect accessed urls to their targetviews.
TARGETS_URLCONF = getsettings('TARGETS_URLCONF', 'linkanalytics.targeturls')

EMAIL_DEFAULT_SUBJECT = getsettings('EMAIL_DEFAULT_SUBJECT', '[No Subject]')
                                          
URLFIELD_LENGTH = getsettings('URLFIELD_LENGTH', 3000)

# A digest constructor used in calculating cryptographic hashes, such as for 
# hashed urls.
import hashlib
DIGEST_CTOR = hashlib.sha1

EMAIL_SUBJECT_LENGTH = getsettings('EMAIL_SUBJECT_LENGTH', 256)

EMAIL_DEFAULT_INCLUDE_PIXELIMG = getsettings('EMAIL_DEFAULT_INCLUDE_PIXELIMG',
                                             True)
                                             
EMAIL_TRACKEDURL_NAMEFORMAT = getsettings('EMAIL_TRACKEDURL_NAMEFORMAT', 
                                          '_email_{0}')

URLBASE_VARNAME = 'urlbase'
LINKID_VARNAME = 'linkid'






