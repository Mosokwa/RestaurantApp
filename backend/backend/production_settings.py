"""
Django production settings for Render deployment
"""
import os
import dj_database_url
from .settings import *  # Import base settings

# =====================
# Security Settings
# =====================
DEBUG = False

# Get secret key from environment (Render will provide)
SECRET_KEY = os.environ.get('SECRET_KEY')

# Render and Netlify domains
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    '.netlify.app',
]

# =====================
# Database (Render PostgreSQL)
# =====================
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',  # Fallback for local dev
        conn_max_age=600
    )
}

# =====================
# CORS for Production
# =====================
CORS_ALLOWED_ORIGINS = [
    "https://your-customer-app.netlify.app",
    "https://your-owner-app.netlify.app",
]

# Or allow all for demo (remove in real production)
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://your-customer-app.netlify.app",
    "https://your-owner-app.netlify.app",
    "https://*.onrender.com",
]

# =====================
# Disable Unsupported Services
# =====================
# Comment out Redis/Celery for demo (Render free tier doesn't include Redis)
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer'
#     }
# }

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }

# Disable Celery for demo
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None

# =====================
# Static Files
# =====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Disable Whitenoise for now (can add later)
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =====================
# Email Settings
# =====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For demo

# =====================
# Logging (disable file logging on Render)
# =====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# =====================
# Production Security Headers
# =====================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# =====================
# Social Auth - Disable for Demo
# =====================
# Remove or comment out social auth providers for demo
# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''
# SOCIAL_AUTH_FACEBOOK_KEY = ''
# SOCIAL_AUTH_FACEBOOK_SECRET = ''

# =====================
# Simplify for Demo
# =====================
# Use simpler password validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Reduced for demo
        }
    },
]

# Simpler throttling for demo
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/day',
    'user': '10000/day',
}