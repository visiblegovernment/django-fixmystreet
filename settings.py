# Django settings for fixmystreet project.
import os
import logging

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
POSTGIS_TEMPLATE = 'template_postgis'

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
    filename = '/tmp/fixmystreet.log',
    filemode = 'w'
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# ensure large uploaded files end up with correct permissions.  See
# http://docs.djangoproject.com/en/dev/ref/settings/#file-upload-permissions

FILE_UPLOAD_PERMISSIONS = 0644
DATE_FORMAT = "l, F jS, Y"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

# include request object in template to determine active page
TEMPLATE_CONTEXT_PROCESSORS = (
  'django.core.context_processors.request',
  'django.contrib.auth.context_processors.auth',
  'django.core.context_processors.csrf',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.middleware.csrf.CsrfResponseMiddleware',
    'mainapp.middleware.subdomains.SubdomainMiddleware',
    'mainapp.middleware.SSLMiddleware.SSLRedirect',
)


LANGUAGES = (
  ('en','English'),
  ('fr', 'French'),
)


ROOT_URLCONF = 'fixmystreet.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.gis',
    'registration',
    'google_analytics',
    'transmeta',
    'social_auth',
    'mainapp',
)

AUTH_PROFILE_MODULE = 'mainapp.UserProfile'

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
#    'social_auth.backends.google.GoogleOAuthBackend',
#    'social_auth.backends.google.GoogleOAuth2Backend',
#    'social_auth.backends.google.GoogleBackend',
#    'social_auth.backends.yahoo.YahooBackend',
#    'social_auth.backends.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
#    'mainapp.tests.testsocial_auth.dummy_socialauth.DummyBackend',
)

CACHE_MIDDLEWARE_ANONYMOUS_ONLY =True
SOCIAL_AUTH_USER_MODEL = 'mainapp.FMSUser'
SOCIAL_AUTH_ASSOCIATE_BY_MAIL = True
ACCOUNT_ACTIVATION_DAYS = 14
SOCIAL_AUTH_EXTRA_DATA = False
SOCIAL_AUTH_COMPLETE_URL_NAME = 'socialauth_complete'
LOGIN_ERROR_URL = '/accounts/login/error/'
SOCIAL_AUTH_ERROR_KEY = 'socialauth_error'
LOGIN_REDIRECT_URL = '/accounts/home/'
LOGIN_DISABLED = True

#################################################################################
# These variables Should be defined in the local settings file
#################################################################################
#
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.contrib.gis.db.backends.postgis',
#        'NAME': '',
#        'USER': '',
#        'PASSWORD': ''
#    }
#}
#
#EMAIL_USE_TLS =
#EMAIL_HOST =
#EMAIL_HOST_USER =
#EMAIL_HOST_PASSWORD =
#EMAIL_PORT =
#EMAIL_FROM_USER =
#DEBUG =
#LOCAL_DEV =
#SITE_URL = http://localhost:8000
#SECRET_KEY=
#GMAP_KEY=
#
#ADMIN_EMAIL =
#ADMINS =
#
# ----- social_auth consumer id's ----- #
#TWITTER_CONSUMER_KEY         = ''
#TWITTER_CONSUMER_SECRET      = ''
#FACEBOOK_APP_ID              = ''
#FACEBOOK_API_SECRET          = ''
#####################################################################################

# import local settings overriding the defaults
# local_settings.py is machine independent and should not be checked in

try:
    from local_settings import *
except ImportError:
    try:
        from mod_python import apache
        apache.log_error( "local_settings.py not set; using default settings", apache.APLOG_NOTICE )
    except ImportError:
        import sys
        sys.stderr.write( "local_settings.py not set; using default settings\n" )


# Using django_testview from here (add 'TESTVIEW' to your local settings): 
# https://github.com/visiblegovernment/django_testview

if DEBUG and globals().has_key('TESTVIEW'):
    INSTALLED_APPS += ('django_testview',)


if DEBUG:
    SOCIAL_AUTH_IMPORT_BACKENDS = (
                                   'mainapp.tests.testsocial_auth',
                                   )
