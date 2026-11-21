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
STATIC_ROOT = BASE_DIR / "staticfiles"
