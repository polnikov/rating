import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = ['www.fiegh-raiting.ru', 'fiegh-raiting.ru', '188.225.79.76', 'localhost']

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['www.fiegh-raiting.ru', 'fiegh-raiting.ru', '188.225.79.76']

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

LOCALE_PATHS = (
    os.path.join(os.path.dirname(__file__), "locale"),
)

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

    "root": {"level": "WARNING", "handlers": ["file"]},

    "formatters": {
        "app": {
            "format": '%(asctime)s %(name)-12s %(levelname)-8s (%(module)s.%(funcName)s) %(message)s',
            "datefmt": "%Y/%m/%d %H:%M:%S",
        },
    },

    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "/var/log/django.log",
            "formatter": "app",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True
        },
    },
}

IMPORT_DELIMITER = ';'

SITE_ID = 1

# debug_toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
