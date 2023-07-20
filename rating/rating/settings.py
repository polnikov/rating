import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = [os.getenv('HOST_IP_EXT'), os.getenv('HOST_IP_INT'), os.getenv('HOST_GASU'), 'localhost']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # user apps
    'archive.apps.ArchiveConfig',
    'dashboard.apps.DashboardConfig',
    'groups.apps.GroupsConfig',
    'students.apps.StudentsConfig',
    'subjects.apps.SubjectsConfig',
    'api.apps.ApiConfig',

    # add apps
    'stronghold',
    'import_export',
    'semanticuiforms',
    'django_better_admin_arrayfield',
    'rest_framework',
]

IMPORT_EXPORT_USE_TRANSACTIONS = True  # import_export package

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # add
    'stronghold.middleware.LoginRequiredMiddleware',
    'django_currentuser.middleware.ThreadLocalUserMiddleware',
    'rating.middleware.ShowMessageMiddleware',
]

ROOT_URLCONF = 'rating.urls'

LOGIN_REDIRECT_URL = '/groups/cards'

LOGOUT_REDIRECT_URL = '/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries':{
                'customfilters': 'templatetags.customfilters',
            }
        },
    },
]

WSGI_APPLICATION = 'rating.wsgi.application'

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DATABASES_NAME_PROD'),
        'USER': os.getenv('DATABASES_USER_PROD'),
        'PASSWORD': os.getenv('DATABASES_PASSWORD_PROD'),
        'HOST': os.getenv('DATABASES_HOST_PROD'),
        'PORT': os.getenv('DATABASES_PORT_PROD'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DATE_FORMAT = DATE_INPUT_FORMATS = DATETIME_INPUT_FORMATS = ['%d.%m.%Y']

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, '/media')

STATIC_URL = '/staticfiles/'

STATIC_ROOT = '/home/code/staticfiles'

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "root": {"level": "INFO", "handlers": ["file"]},

    "formatters": {
        "app": {
            "format": '%(asctime)s %(name)-12s %(levelname)-8s (%(module)s.%(funcName)s) %(message)s',
            "datefmt": "%Y/%m/%d %H:%M:%S",
        },
    },

    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/django.log",
            "formatter": "app",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True
        },
    },
}

IMPORT_DELIMITER = ';'

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

SESSION_COOKIE_AGE = timedelta(days=1).total_seconds()
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
