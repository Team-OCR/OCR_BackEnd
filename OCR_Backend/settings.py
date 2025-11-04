"""
Django settings for OCR_Backend project.
"""

from pathlib import Path
import os

# --------------------------------------------------------------
# Build paths
# --------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------
# Security
# --------------------------------------------------------------
SECRET_KEY = 'django-insecure-z$(qx=+1ya53f2rh_gs_8*230yp$(mvi5r44d7b2h8%y8=6b(9'
DEBUG = True
ALLOWED_HOSTS = ['*']                     # OK for local dev only

# --------------------------------------------------------------
# Applications
# --------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',      # <-- DRF
    'corsheaders',
    'ocr_module',          # <--  OCR module
]

# --------------------------------------------------------------
# Middleware
# --------------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'OCR_Backend.urls'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",      # Vite / CRA
    "http://127.0.0.1:3000",
]
# --------------------------------------------------------------
# Templates
# --------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # <-- global template folder
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

WSGI_APPLICATION = 'OCR_Backend.wsgi.application'

# --------------------------------------------------------------
# Database
# --------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --------------------------------------------------------------
# Password validation
# --------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------
# Internationalisation
# --------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------
# Static files
# --------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # collectstatic target (optional)

# --------------------------------------------------------------
# Media (uploaded files)
# --------------------------------------------------------------
MEDIA_URL = '/files/'
MEDIA_ROOT = BASE_DIR / 'files'          # <-- note: Path object

# --------------------------------------------------------------
# Django REST Framework – **Browsable API** + parsers
# --------------------------------------------------------------
REST_FRAMEWORK = {
    # Renderers – JSON + the nice HTML form
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Parsers – needed for multipart file uploads
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# --------------------------------------------------------------
# Default primary key
# --------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'