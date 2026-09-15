import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('DJANGO_ENV', 'development').lower() == 'production':
        raise RuntimeError('DJANGO_SECRET_KEY deve ser definida em produção.')
    SECRET_KEY = 'local-development-only-change-me'
DEBUG = os.environ.get('DJANGO_DEBUG', 'false').lower() == 'true'
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if host.strip()]
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'false').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'false').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'false').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'false').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'false').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'extractor']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 'extractor.middleware.SecurityAuditMiddleware',
]
ROOT_URLCONF = 'medextract.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'medextract.wsgi.application'
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
if DATABASE_URL.startswith(('postgres://', 'postgresql://')):
    database_url = urlparse(DATABASE_URL)
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': database_url.path.lstrip('/'), 'USER': database_url.username, 'PASSWORD': database_url.password, 'HOST': database_url.hostname, 'PORT': database_url.port or 5432}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.environ.get('DJANGO_DB_PATH', str(BASE_DIR / 'db.sqlite3'))}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = 'media/'
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', 12 * 1024 * 1024))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'dashboard'
API_TOKEN_LIFETIME = timedelta(days=int(os.environ.get('API_TOKEN_LIFETIME_DAYS', '30')))
DEMO_RETENTION_HOURS = int(os.environ.get('DEMO_RETENTION_HOURS', '24'))
AUDIT_RETENTION_DAYS = int(os.environ.get('AUDIT_RETENTION_DAYS', '365'))
PRESCRIPTION_RETENTION_DAYS = int(os.environ.get('PRESCRIPTION_RETENTION_DAYS', '730'))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('RATE_LIMIT_WINDOW_SECONDS', '60'))
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get('RATE_LIMIT_MAX_REQUESTS', '60'))
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.environ.get('LOGIN_RATE_LIMIT_MAX_ATTEMPTS', '5'))
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('LOGIN_RATE_LIMIT_WINDOW_SECONDS', '900'))
ALERT_WEBHOOK_URL = os.environ.get('ALERT_WEBHOOK_URL', '').strip()
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'console': {'class': 'logging.StreamHandler'}}, 'loggers': {'django.security': {'handlers': ['console'], 'level': 'WARNING'}, 'extractor': {'handlers': ['console'], 'level': os.environ.get('LOG_LEVEL', 'INFO')}}}
