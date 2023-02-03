"""
Django settings for ecommerce project.

Generated by 'django-admin startproject' using Django 3.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", default="development")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", default="1")

ALLOWED_HOSTS = ['www.foexgroupsrl.com.ar']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # The following apps are required for allauth
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sites',

    # allauth - used to manage login
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # crispy - used to create forms
    'crispy_forms',

    # django startproject
    'main_app',

    # localflavor - used for modeling specific fields in models and forms
    'localflavor',

    # mercadopago - used to perform payments
    'mercadopago_payment.apps.MercadopagoPaymentConfig',

    # to generate database diagram
    'django_extensions',

    # 'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'mercadopago_payment.middleware.open_access_middleware'
    # 'corsheaders.middleware.CorsMiddleware',
]

## CORS is used to allow cross-site accesses
# CORS_ORIGIN_ALLOW_ALL = False
# CORS_ORIGIN_WHITELIST = (
#     'https://viacep.com.br',
# )

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                # `allauth` needs this from django
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# If you want to use a simple database without docker uncomment these lines and comment the postgresql lines below
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#         # 'ATOMIC_REQUESTS': True
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'foexgroup_db',
        'USER': 'foexgroup',
        'PASSWORD': '1234Foex!',
        'HOST': 'db',
        'PORT': 5432,
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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

#LANGUAGE_CODE = 'pt-BR'
#CURRENCY = 'BRL'

# --- Cambio JMRG ---

LANGUAGE_CODE = 'es-AR'
CURRENCY = '$'


# https://www.mercadopago.com.br/ajuda/minimo-maximo-posso-pagar-pelo_324
MERCADOPAGO_MAXVALUE_CREDITCARD = 60000.0
MERCADOPAGO_MINVALUE_CREDITCARD = 0.5


# --- Cambio JMRG --- TIME_ZONE = 'America/Sao_Paulo'
TIME_ZONE = 'America/Buenos_Aires'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Needed to login by username in Django admin, regardless of `allauth`
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Used to provide access to allauth
SITE_ID = 1

LOGIN_REDIRECT_URL = '/'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

# email configuration: https://stackoverflow.com/questions/29840595/how-can-i-figure-out-why-django-allauth-isnt-sending-a-confirmation-e-mail
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACCOUNT_EMAIL_VERIFICATION = "none"

# Lib used by Crispy to create forms automatically - crispy is being used in the html templates: form|crispy
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

MERCADO_PAGO_PUBLIC_KEY = os.environ.get("MERCADO_PAGO_PUBLIC_KEY", default="")
MERCADO_PAGO_ACCESS_TOKEN = os.environ.get("MERCADO_PAGO_ACCESS_TOKEN", default="")