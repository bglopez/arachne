# -*- coding: utf-8 -*-

"""Django settings for the Arachne site.
"""
import os
# Debug settings. Set this to False in a production environment.
DEBUG = False
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.  If
# running in a Windows environment this must be set to the same as your system
# time zone.
TIME_ZONE = 'America/Los_Angeles'

# Sssh... Tell no one
SECRET_KEY = 'bkl_i@q9n813@hvt-*&2wnsvh&4cv+%f46qvdzoqn&i7l7bi3y'

# Absolute path to the database directory. This should match the value in
# /etc/arachne/daemon.conf.
ARACHNE_DATABASE_DIR = '/data/arachne/root/lib'

# Absolute path to a file where the search log should be located.  If set to an
# empty string logging is disabled.
ARACHNE_SEARCH_LOG = ''

# Path, from the root of the site, where the Arachne site is located.
ARACHNE_ROOT = '/data/arachne/django/arachnesite/arachneapp/'

# URL where the Arachne media is located. The leading / is required!
ARACHNE_MEDIA_URL = '/data/arachne/django/arachnesite/arachneapp/media/'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# If you set this to False, Django will make some optimizations so as not to
# load the internationalization machinery.
USE_I18N = False

# Full name of the URLconf root module.
ROOT_URLCONF = 'urls'

# List of strings representing installed apps.
INSTALLED_APPS = (
    'arachneapp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

# Add the path to the directory with the templates here.
TEMPLATE_DIRS = (
    os.path.join(ARACHNE_ROOT, '/templates'),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ARACHNE_ROOT, '/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# We don't need any context processor.
TEMPLATE_CONTEXT_PROCESSORS = ()

# This site does not need any middleware but leave this as sugested in the
# Django documentation.
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)
