#!/usr/bin/env bash

python manage.py migrate --settings=$DJANGO_SETTINGS_MODULE --noinput
python manage.py collectstatic --settings=$DJANGO_SETTINGS_MODULE --noinput
django-admin compilemessages
python -m gunicorn --bind=0.0.0.0 --timeout 600 rechnung.wsgi
