# Django settings for bigpeople project.
import os.path
from platform import platform

PROJECT_TITLE= 'Big People'

ROOT_PATH = os.path.normpath( os.path.dirname(__file__) )

DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('admin1', 'none@none.net'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_engine', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bigpeople',             # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation.
TIME_ZONE = 'Asia/Almaty'

# Default interface language.
DEFAULT_LANG = 'Russian'

# Text duration in milliseconds
TEXT_DUR_FLOOR = 77000
TEXT_DUR_CEIL = 83000

# Language code for this installation.
LANGUAGE_CODE = 'en-us'

# Don't load the internationalization machinery.
USE_I18N = False

# Format dates, numbers and calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Thumbnail size
THUMBNAIL_SIZE = (180, 180)

# Upload filename length
FILENAME_LEN = 15

LOGIN_URL = '/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT = os.path.join( ROOT_PATH, 'site_media/' )

# URL that handles the media served from MEDIA_ROOT.
# for development period only!!!
MEDIA_URL = '/site_media/'

# Absolute path to the directory static files should be collected to.
STATIC_ROOT = os.path.join( ROOT_PATH, 'static/' )

# URL prefix for static files.
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# ADMIN_MEDIA_PREFIX = '/static/admin/'
ADMIN_MEDIA_PREFIX = '/site_media/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages"
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'bigpeople.urls'

TEMPLATE_DIRS = (
    os.path.join( ROOT_PATH, 'templates/' ),
)

AUTHENTICATION_BACKENDS = (
    'permission_backend_nonrel.backends.NonrelPermissionBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_mongodb_engine',
    'djangotoolbox',
    'permission_backend_nonrel',
    'bigpeople.browser',
    'bigpeople.screenwriter',
    'bigpeople.interpreter',
    'bigpeople.api',
)

# A sample logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

try:
    from local_settings import *
except ImportError:
    pass
