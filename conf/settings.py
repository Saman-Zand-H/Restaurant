import os
import sys
import socket
from environs import Env
from pathlib import Path
from rich.logging import RichHandler


BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'apps'))

env = Env()
env.read_env()


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', 0)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '*'
]
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:800',
    'http://locahost:8000',
]


USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 
                           'http' if DEBUG else 'https')


# Application definition

INSTALLED_APPS = [
    'djangocms_admin_style',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.gis',
    
    'users.apps.UsersConfig',
    
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'azbankgateways',
    'channels',
    'channels_redis',
    'crispy_forms',
    'debug_toolbar',
    # 'django_elasticsearch_dsl',
    'django_extensions',
    'django_filters',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'iranian_cities',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'webpush',
    'drf_yasg',
    
    # django-cms
    'cms',
    'menus',
    'sekizai',
    'treebeard',
    'djangocms_text_ckeditor',
    'filer',
    'easy_thumbnails',
    'aldryn_apphooks_config',
    'parler',
    'taggit',
    'taggit_autosuggest',
    'meta',
    'sortedm2m',
    'djangocms_blog',
    'djangocms_bootstrap4',
    'djangocms_bootstrap4.contrib.bootstrap4_alerts',
    'djangocms_bootstrap4.contrib.bootstrap4_badge',
    'djangocms_bootstrap4.contrib.bootstrap4_card',
    'djangocms_bootstrap4.contrib.bootstrap4_carousel',
    'djangocms_bootstrap4.contrib.bootstrap4_collapse',
    'djangocms_bootstrap4.contrib.bootstrap4_content',
    'djangocms_bootstrap4.contrib.bootstrap4_grid',
    'djangocms_bootstrap4.contrib.bootstrap4_jumbotron',
    'djangocms_bootstrap4.contrib.bootstrap4_link',
    'djangocms_bootstrap4.contrib.bootstrap4_listgroup',
    'djangocms_bootstrap4.contrib.bootstrap4_media',
    'djangocms_bootstrap4.contrib.bootstrap4_picture',
    'djangocms_bootstrap4.contrib.bootstrap4_tabs',
    'djangocms_bootstrap4.contrib.bootstrap4_utilities',
    'djangocms_file',
    'djangocms_icon',
    'djangocms_link',
    'djangocms_picture',
    'djangocms_style',
    'djangocms_video',
    
    'api',
    'delivery',
    'in_place',
    'restaurants',
    'search_index',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'cms.middleware.utils.ApphookReloadMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
]

ROOT_URLCONF = 'conf.urls'

TEMPLATES_DIR = os.path.join(CORE_DIR, 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            TEMPLATES_DIR,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'sekizai.context_processors.sekizai',
                'django.template.context_processors.static',
                'cms.context_processors.cms_settings'
            ],
        },
    },
]

ASGI_APPLICATION = 'conf.asgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env.str('DB_NAME', 'postgres'),
        'USER': env.str('DB_USER', 'postgres'),
        'PASSWORD': env.str('DB_PASSWORD', 'postgres'),
        'HOST': env.str('DB_HOST', 'db'),
        'PORT': env.int('DB_PORT', 5432),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_USER_MODEL = 'users.UserModel'

ADMINS = (
    ('Saman', 'samanzand84@gmail.com'),
)


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
]

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(CORE_DIR, 'static')]
STATIC_ROOT = os.path.join(CORE_DIR, os.path.join('staticfiles'))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(CORE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

# logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - [%(levelname)s]    %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'rich.logging.RichHandler',
            'formatter': 'default'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': 'logs/app/app.log'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'class': 'rich.logging.RichHandler',
        }
    }
}


# email config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST', 'smtp-relay.sendinblue.com')
EMAIL_PORT = env.int('EMAIL_PORT', 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')


# allauth configurations
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USER_MODEL_SIGNUP_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_ADAPTER = 'users.adapters.AccountAdapter'
ACCOUNT_FORMS = {
    'signup': 'users.forms.SignupForm',
    'login': 'users.forms.LoginForm',
}
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online'
        }
    }
}

# seleniumlogin conf
SELENIUM_LOGIN_START_PAGE = '/accounts/login/'

# crispy forms configurations
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# djdt configuration
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1', '10.0.2.2']


# celery configurations
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', 
                            'amqp://guest:guest@rabbitmq')
CELERY_RESULT_BACKEND = env.str('CELERY_RESULT_BACKEND', 
                                'rpc://')
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


# elasticsearch configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env.str('ELASTICSEARCH_SOCKET', 'elasticsearch:9200'),
        'refresh_interval': 10
    },
}


# DRF configurations
JWT_AUTH_COOKIE = 'rubik'
JWT_AUTH_REFRESH_COOKIE = 'rubik-refresh'
REST_USE_JWT = True
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_AUTO_SCHEMA_CLASS': 'rest_framework_gis.schema.GeoFeatureAutoSchema',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_gis.schema.GeoFeatureAutoSchema',
}
SWAGGER_SETTINGS = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_gis.schema.GeoFeatureAutoSchema'
}


# Django Channels Configuration
REDIS_BACKEND = env.str('REDIS_BACKEND', 'redis')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_BACKEND, 6379)]
        }
    }
}


# Bank Gateway Configurations
AZ_IRANIAN_BANK_GATEWAYS = {
    'GATEWAYS': {
        'ZIBAL': {
            'MERCHANT_CODE': 'zibal'
        }
    },
    'IS_SAMPLE_FORM_ENABLE': DEBUG,
    'DEFAULT': 'ZIBAL',
}


# webpush settings
WEBPUSH_SETTINGS = {
    'VAPID_PUBLIC_KEY': env.str('VAPID_PUBLIC_KEY'),
    'VAPID_PRIVATE_KEY': env.str('VAPID_PRIVATE_KEY'),
    'VAPID_ADMIN_EMAIL': env.str('VAPID_ADMIN_EMAIL', 
                                 'tnsperuse@gmail.com')
}


# django-cms configurations
CMS_LANGUAGES = {
    ## Customize this
    1: [
        {
            'code': 'en',
            'name': 'en',
            'redirect_on_fallback': True,
            'public': True,
            'hide_untranslated': False,
        },
    ],
    'default': {
        'redirect_on_fallback': True,
        'public': True,
        'hide_untranslated': False,
    },
}
CMS_TEMPLATES = (
    ('cms/fullwidth.html', 'Fullwidth'),
    ('cms/sidebar_left.html', 'Sidebar Left'),
    ('cms/sidebar_right.html', 'Sidebar Right')
)
THUMBNAIL_HIGH_RESOLUTION = True
CMS_PAGE_CACHE = False
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters'
)
X_FRAME_OPTIONS = 'SAMEORIGIN'
CMS_PERMISSION = True
CMS_PLACEHOLDER_CONF = {}

META_SITE_PROTOCOL = 'https' if env.bool('production', 1) else 'http'
META_SITE_DOMAIN = env.str('domain', 'example.com')
