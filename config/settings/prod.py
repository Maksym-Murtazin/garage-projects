import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY.strip() or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a private production key.")

ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS to your deployment hostnames.")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
MIDDLEWARE = [*MIDDLEWARE]
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
STATIC_ROOT = BASE_DIR / "staticfiles"


def required_database_setting(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"Set {name} for the production PostgreSQL database.")
    return value


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required_database_setting("POSTGRES_DB"),
        "USER": required_database_setting("POSTGRES_USER"),
        "PASSWORD": required_database_setting("POSTGRES_PASSWORD"),
        "HOST": required_database_setting("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_DB_PORT", "5432"),
        "OPTIONS": {"sslmode": "require", "channel_binding": "require"},
        # Neon pooled connections use transaction pooling.
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}
