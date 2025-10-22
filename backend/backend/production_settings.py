"""
Django production settings for Render deployment
"""
import os
import dj_database_url
from .settings import *  # Import everything from base settings

# =====================
# Security Settings
# =====================
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

# Production domains
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    '.netlify.app',
]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# =====================
# Database (Render PostgreSQL)
# =====================
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        ssl_require=True
    )
}

# =====================
# CORS for Production
# =====================
CORS_ALLOWED_ORIGINS = [
    "https://restaurantsowners.netlify.app/",
    "https://restaurantscustomers.netlify.app/",
    "https://restaurantapp-1-t269.onrender.com",
]

# Or allow all for demo simplicity
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://restaurantsowners.netlify.app/",
    "https://restaurantscustomers.netlify.app/",
    "https://restaurantapp-1-t269.onrender.com",
]

# =====================
# Social Auth - KEEP YOUR CREDENTIALS
# =====================

# Google OAuth2 - Use environment variables
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID', '')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']

# Facebook OAuth2 - Use environment variables
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

# Update redirect URLs for production
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://restaurantapp-1-t269.onrender.com/accounts/google/login/callback/'
SOCIAL_AUTH_FACEBOOK_REDIRECT_URI = 'https://restaurantapp-1-t269.onrender.com/accounts/facebook/login/callback/'

# Allauth providers (keep your existing config)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
        ],
        'EXCHANGE_TOKEN': True,
    }
}

# =====================
# Disable Unsupported Services for Demo
# =====================

# Disable Redis/Channels (Render free tier doesn't include Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Disable Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Disable Celery (no Redis broker available)
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None

# =====================
# Static Files
# =====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add Whitenoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =====================
# Email Settings for Production
# =====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For demo

# =====================
# Logging (Console-only for Render)
# =====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =====================
# Simplify for Production Demo
# =====================

# Simpler password validation for demo
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Reduced for demo convenience
        }
    },
]

# Simpler throttling for demo
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/day',
    'user': '10000/day',
    'auth': '100/minute',
    'password_reset': '100/hour',
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
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# =====================
# Application Specific
# =====================
# Update frontend URL for production
FRONTEND_URL = 'https://your-restaurant-customer.netlify.app'

# Use HTTPS for OAuth and social auth
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Change to 'mandatory' in real production

print("=== USING PRODUCTION SETTINGS ===")
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"DATABASE: {DATABASES['default']['ENGINE']}")
print(f"Social Auth: Enabled")