#!/usr/bin/env bash

python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compilemessages
gunicorn --bind=0.0.0.0:8000 rechnung.wsgi:application
