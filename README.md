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

To start the server with the provided docker compose file use the following command:
`docker compose up`
However, you need to set up a few environment variables.

| Env Var              | Value                                                                                                                                         |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| SECRET_KEY           | Security string. Must not be shared.                                                                                                          |
| ALLOWED_HOSTS        | List of you hostname you want to access the application. E.g. `example.com,10.56.120.9`.                                                      |
| DATABASE_URL         | Database URL.                                                                                                                                 |
| CSRF_TRUSTED_ORIGINS | (Optional, Default: `http://*,https://*`) Used for endpoint names under which the server can be targeted. This is required for POST requests. |
