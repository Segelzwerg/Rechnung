# Rechnung

[![Tests](https://github.com/Segelzwerg/Rechnung/actions/workflows/django.yml/badge.svg)](https://github.com/Segelzwerg/Rechnung/actions/workflows/django.yml)
[![Documentation Status](https://readthedocs.org/projects/rechnung-django/badge/?version=latest)](https://rechnung-django.readthedocs.io/en/latest/?badge=latest)
![Codecov](https://img.shields.io/codecov/c/github/Segelzwerg/Rechnung)
![GitHub repo size](https://img.shields.io/github/repo-size/Segelzwerg/Rechnung)
![GitHub Release Date](https://img.shields.io/github/release-date/Segelzwerg/Rechnung)
![GitHub License](https://img.shields.io/github/license/Segelzwerg/Rechnung)

![Static Badge](https://img.shields.io/badge/translation-German-brightgreen)

Django App for invoices

Check out our [documentation](https://rechnung-django.readthedocs.io/en/latest/)

## Docker Compose

To start the server with the docker compose file. Use the following command:
`docker compose up`
However, you need to set up a few environment variables.

| Env Var                | Value                                                                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| DJANGO_SETTINGS_MODULE | The path to the django settings file you want to use. This should be `rechnung.prod_settings` if you don't require customizations.      |
| ALLOWED_HOSTS          | List of you hostname you want to access the application. E.g. `"['0.0.0.0']"`.                                                          |
| SECRET_KEY             | Security string. Must not be shared.                                                                                                    |
| CSRF_TRUSTED_ORIGINS   | (Optional, Default: `http://0.0.0.0`) Used for endpoint names under which the server can be target. This is required for POST requests. |
| DB_NAME                | Any name of the database.                                                                                                               |
| DB_USER                | Name of the admin.                                                                                                                      |
| DB_PASSWORD            | Password of the admin.                                                                                                                  |
| DB_HOST                | Hostname of the database. It must be the same as docker compose service.                                                                |
| DB_PORT                | Port of the database.                                                                                                                   |
