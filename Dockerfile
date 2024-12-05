ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION} AS poetry
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt
LABEL authors="Segelzwerg"

FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=poetry /app/requirements.txt .
RUN apt-get update
RUN apt-get install gettext -y
RUN pip install -r requirements.txt
COPY invoice ./invoice/
COPY rechnung ./rechnung/
#COPY static/ ./static/
COPY templates/ ./templates/
COPY manage.py ./manage.py
CMD python manage.py migrate --settings=$DJANGO_SETTINGS_MODULE; python manage.py collectstatic --no-input --settings=$DJANGO_SETTINGS_MODULE; django-admin compilemessages; gunicorn --bind=0.0.0.0 --timeout 600 rechnung.wsgi
