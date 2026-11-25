#!/usr/bin/env bash
set -o errexit

if [[ ${DJANGO_SETTINGS_MODULE:-} != config.settings.prod ]]; then
    echo "Set DJANGO_SETTINGS_MODULE=config.settings.prod before building." >&2
    exit 1
fi

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
