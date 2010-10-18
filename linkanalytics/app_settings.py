import os.path

from django.conf import settings

#==============================================================================#
# Do not change the defaults in this file.  To modify the settings for your own
# deployment, define the setting (with "LINKANALYTICS_" prefix) in your
# project's settings.py.

#==============================================================================#
def getsettings(name, default):
    """Wrapper around the builtin getattr() which returns the value from
       settings.LINKANALYTICS_<name>."""
    return getattr(settings, 'LINKANALYTICS_{0}'.format(name), default)

#==============================================================================#
# The settings:

# Base url in Linkanalytics app (everything before the '/linkanalytics/...')
# It must NOT include a trailing slash.
URLBASE = settings.LINKANALYTICS_URLBASE

# Where to find the pixel images.  The default is the media subdirectory.
PIXEL_IMGDIR = getsettings('PIXEL_IMGDIR', 'linkanalytics/media')

# TODO:
# optional custom targeturls module (so user can add his/her own views)
# extra targetviews directory? (so user can non-intrusively override
#                               linkanalytics defaults)


# Assumes that this module is in the linkanalytics app directory, and that its
# __file__ attribute will be an absolute path or a path relative to the current
# working directory.  If none of these conditions are met, one should set the
# LINKANALYTICS_ABSPATHBASE setting appropriately.  Theoretically, you should
# not need to do this unless this module is moved, or unless the working
# directory is changed between starting Django and this module being loaded.
_DEFAULT_BASEPATH = os.path.dirname(os.path.abspath(__file__))

# Absolute path to the linkanalytics app.
ABSPATHBASE = getsettings('ABSPATHBASE', _DEFAULT_BASEPATH)

# Secret key used in hashing URLs.  If LINKANALYTICS_SECRET_KEY is not found or
# evaluates to False, the SECRET_KEY provided in settings.py is used.
SECRET_KEY = getsettings('SECRET_KEY', '')
if not SECRET_KEY:
    SECRET_KEY = settings.SECRET_KEY

# Location of the urlconf used to redirect accessed urls to their targetviews.
TARGETS_URLCONF = getsettings('TARGETS_URLCONF', 'urls')
# 'linkanalytics.targeturls'

# Length of urls stored in the database.
URLFIELD_LENGTH = getsettings('URLFIELD_LENGTH', 3000)

# A digest constructor used in calculating cryptographic hashes, such as for
# hashed urls.  See the 'hashlib' standard module for information.
import hashlib
DIGEST_CTOR = hashlib.sha1

# Variable names used in Django templates when rendering tracked urls.  These
# should not need to be changed.
URLBASE_VARNAME = 'urlbase'
LINKID_VARNAME = 'linkid'

#==============================================================================#
# Email-specific settings:

# Directory below ABSPATHBASE where email app templates are found.  This should
# not need to be changed.
_EMAIL_TEMPLATESDIR = os.path.join('templates', 'linkanalytics', 'email')

# Absolute paths where headers and footers can be found.
EMAIL_HEADERSDIR = getsettings('EMAIL_HEADERSDIR',
                    os.path.join(ABSPATHBASE, _EMAIL_TEMPLATESDIR, 'headers'))
EMAIL_FOOTERSDIR = getsettings('EMAIL_FOOTERSDIR',
                    os.path.join(ABSPATHBASE, _EMAIL_TEMPLATESDIR, 'footers'))

# Length of the subject field in the database.
EMAIL_SUBJECT_LENGTH = getsettings('EMAIL_SUBJECT_LENGTH', 256)

# The value used for an email's subject if it is left blank when it is sent.
EMAIL_DEFAULT_SUBJECT = getsettings('EMAIL_DEFAULT_SUBJECT', '[No Subject]')

# Should emails include a pixel image by default.  This can be modified for 
# individual emails when composing them.
EMAIL_DEFAULT_INCLUDE_PIXELIMG = getsettings('EMAIL_DEFAULT_INCLUDE_PIXELIMG',
                                             True)

# Format string used when creating Trackers representing sent emails.
EMAIL_TRACKER_NAMEFORMAT = getsettings('EMAIL_TRACKER_NAMEFORMAT', '_email_{0}')

#==============================================================================#




