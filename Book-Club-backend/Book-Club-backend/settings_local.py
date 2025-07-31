from .settings import *  # noqa
import os

# Override settings for local development
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Fix URL configuration for local development
ROOT_URLCONF = 'Book-Club-backend.urls'
WSGI_APPLICATION = 'Book-Club-backend.wsgi.application'

# Enhanced logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'myapp': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# CORS settings for local development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://nakara4.github.io",  # Your GitHub Pages frontend
]

CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Database configuration - can be overridden by DATABASE_URL
if not os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_local.sqlite3',
        }
    }

# Static files for local development
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files for local development
MEDIA_ROOT = BASE_DIR / 'media_local'

print("🚀 Local development settings loaded!")
print(f"📍 Frontend CORS origins: {CORS_ALLOWED_ORIGINS}")
print(f"📂 Media root: {MEDIA_ROOT}")
print(f"💾 Database: {'SQLite (local)' if not os.getenv('DATABASE_URL') else 'External DB'}")
