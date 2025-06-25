#!/usr/bin/env bash

django-admin migrate --settings=$DJANGO_SETTINGS_MODULE --noinput
django-admin collectstatic --settings=$DJANGO_SETTINGS_MODULE --noinput
django-admin compilemessages
python -m gunicorn --bind=0.0.0.0 --timeout 600 rechnung.wsgi
