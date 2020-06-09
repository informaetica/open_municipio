# -*- coding: utf-8 -*-
# ## Django global settings for the "OpenMunicipio" web application.
##
## Note that machine-specific settings (such as DB connection parameters,
## absolute filesystem paths, passwords, etc.) should be placed within 
## a separate Python module, beginning with this import statement:
##
## .. code:: python
##     from open_municipio.settings import * 
##
## This way, machine-specific settings override project-level settings.
##
## A common naming scheme for these "overlay" settings files is as follows:
##
## * ``settings_local.py`` -- for development machines
## * ``settings_staging.py`` -- for staging servers
## * ``settings_production.py`` -- for production servers

import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.dirname(PROJECT_ROOT))
VERSION = __version__ = file(os.path.join(PROJECT_ROOT, 'VERSION')).read().strip()

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DJANGO_TOOLBAR = True


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

POLITICIANS_GROUP = "politicians"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Rome'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'it-IT'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

# Root URLconf module for staging servers
ROOT_URLCONF = 'open_municipio.urls'


TEMPLATE_DIRS = (
  os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "open_municipio.om.context_processor.defaults",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "social_auth.context_processors.social_auth_by_name_backends",
    "social_auth.context_processors.social_auth_backends",
    "social_auth.context_processors.social_auth_by_type_backends",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'django_extensions',
    'registration',
    'profiles',
    'south',
    'taggit',
    'voting',
    'haystack',
    'rest_framework',
    'cookielaw',
    'open_municipio.events',
    'open_municipio.inline_edit',
    'open_municipio.autocomplete',
    'open_municipio.om',
    'open_municipio.om_comments',
    'open_municipio.om_voting',
    'open_municipio.bookmarking',
    'open_municipio.acts',
    'open_municipio.people',
    'open_municipio.taxonomy',
    'open_municipio.locations',
    'open_municipio.votations',
    'open_municipio.attendances',
    'open_municipio.users',
    'open_municipio.monitoring',
    'open_municipio.web_services',
    'open_municipio.newscache',
    'open_municipio.data_import',
    'open_municipio.idioticon',
    'open_municipio.newsletter',
    'sorl.thumbnail',
    'social_auth',
    'open_municipio.om_auth',
    'open_municipio.api',
#    'open_municipio.speech',
    # TinyMCE
    'tinymce',
#    'inline_ordering',
)

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'social_auth.backends.contrib.github.GithubBackend',
#    'social_auth.backends.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# ``django-social-auth`` settings
FACEBOOK_EXTENDED_PERMISSIONS = ['email']

LOGIN_URL          = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL    = '/login-error/'


SOCIAL_AUTH_BACKENDS_LIST = {
    'twitter': "Twitter",
    'google-oauth2': "Google",
    'facebook': "Facebook",
}
SOCIAL_AUTH_COMPLETE_URL_NAME  = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'
SOCIAL_AUTH_EXPIRATION = 'expires'
SOCIAL_AUTH_RAISE_EXCEPTIONS = DEBUG
SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.misc.save_status_to_session',
    'open_municipio.om_auth.pipeline.redirect_to_form',
    'open_municipio.om_auth.pipeline.extra_data',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'open_municipio.om_auth.pipeline.create_profile',
    'open_municipio.om_auth.pipeline.update_email',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details',
)



# ``django-registration`` settings
ACCOUNT_ACTIVATION_DAYS = 7 # Activation window
REGISTRATION_AUTO_LOGIN = True

# use app shortcut (app.class)
AUTH_PROFILE_MODULE = 'users.UserProfile'

# comments settings
COMMENTS_APP = 'open_municipio.om_comments'

## settings for the ``open_municipio.bookmarking`` app
# CSS class used to mark DOM elements associated with bookmarked (key) objects 
OM_BOOKMARKING_STAR_CLASS = 'icon-star'
# CSS class used to mark DOM elements associated with bookmarkable (but not-key) objects
OM_BOOKMARKING_EMPTY_STAR_CLASS = 'icon-star-empty'

# Site templates globals variables
SITE_INFO = {
    'main_city': u'City',
    'site_version': u'Beta',
    'main_city_logo': 'img/city-logo/city-logo.png',
    'main_city_website': 'http://www.maincity.it', 
}
DEFAULT_FROM_EMAIL = "info@openmunicipio.it"
DIGEST_DEFAULT_GROUP = "redazione"

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'unique-secret-key-has-been-changed-in-instance-settings'


## settings for the ``open_municipio.om_comments`` app
# Number of second within which users can delete their own comments
OM_COMMENTS_REMOVAL_MAX_TIME = 600

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'console_import':{
            'level':'WARNING',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'logfile': {
            'level':'INFO',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': REPO_ROOT + "/log/logfile",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': [ 'require_debug_false', ],
        },
        'webapp': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': REPO_ROOT + "/log/webapp.log",
            'maxBytes': 50000,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            },
        'import': {
            'handlers': ['console_import', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'webapp': {
            'handlers': [ 'webapp', ],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# configuration for auto-complete of Acts in Calendar
AJAX_LOOKUP_CHANNELS = {
    'calendar_act' : { 'model' : 'acts.Act', 'search_field':'title' }
}

AJAX_SELECT_BOOTSTRAP = True
AJAX_SELECT_INLINES = 'inline'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'sitestatic')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# override this in your local open_municipio installation
WEB_SERVICES = {
    'google_analytics': '',
    'facebook' : {},
    'twitter' : {},
    'google_plus': {},
}

# custom TinyMCE stylesheet
TINYMCE_DEFAULT_CONFIG = {
    'content_css': '/static/css/tinymce-content.css',
}


# the UI_* configurations are passed by the default context processor
UI_SITTINGS_CALENDAR = True
UI_LOCATIONS = True
UI_ALLOW_NICKNAMES = True

# act search by type urls
SEARCH_URLS = {
    "council_deliberation": "/acts/?q=&f=act_type:delibera",
    "cg_deliberation": "/acts/?q=&f=act_type:delibera di giunta",
    "interrogation": "/acts/?q=&f=act_type:interrogazione",
    "motion": "/acts/?q=&f=act_type:mozione",
    "agenda": "/acts/?q=&f=act_type:ordine del giorno",
    "interpellation": "/acts/?q=&f=act_type:interpellanza",
    "interrogation": "/acts/?q=&f=act_type:interrogazione",
    "amendment": "/acts/?q=&f=act_type:emendamento",
    "audit": "/acts/?q=&f=act_type:accesso agli atti",
}

CONTACTS_EMAIL = "info@openmunicipio.it"

WEBMASTER_INFO = {
    'name': u'OpenPolis',
    'website': u'http://www.openmunicipio.it',
    'address': u'...',
    'email': u'info@openmunicipio.it',
    'phone': u'',
}

# links to social sites related to OM
SOCIAL_SITES = {
    'twitter': '', # e.g. 'https://twitter.com/<your_twitter_account>',
    'facebook': '', # e.g. 'https://www.facebook.com/<your_facebook_account>',
}

OM_START_YEAR = 2008

OP_URL_TEMPLATE = "http://politici.openpolis.it/politico/%(op_id)s"

NL_TITLE = "Monitoraggio Open Municipio"
NL_FROM = "Open Municipio <noreply@openmunicipio.it>"

# allow to show an alert on the homepage of openmunicipio
ALERT_POPUP = ""
ALERT_BAR = ""
ALERT_NAVBAR = ""

# this is a default configuration for a local instance of Solr running;
# adapt this to your production environment
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr',
        'TIMEOUT': 60 * 15,
        'BATCH_SIZE': 100,
        'SEARCH_RESULTS_PER_PAGE': HAYSTACK_SEARCH_RESULTS_PER_PAGE,
    }
}

SOUTH_MIGRATION_MODULES = {
    'acts': 'open_municipio.acts.migrations',
    'votations': 'open_municipio.votations.migrations',
    'people': 'open_municipio.people.migrations',
    'users': 'open_municipio.users.migrations',
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'open_municipio.api.pagination.StandardPagination',   
}

SHOW_ADVANCED_GRAPH = False
