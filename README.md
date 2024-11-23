# Rechnung

Django App for invoices

## Docker Compose

To start the server with the docker compose file. Use the following command:
`docker compose up`
However, you need to set up a few environment variables.

| Env Var                | Value                                                                                                                              |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| DJANGO_SETTINGS_MODULE | The path to the django settings file you want to use. This should be `rechnung.prod_settings` if you don't require customizations. |
| ALLOWED_HOSTS          | List of you hostname you want to access the application. E.g. `"['0.0.0.0']"`.                                                     |
| SECRET_KEY             | Security string. Must not be shared.                                                                                               |
| DB_NAME                | Any name of the database.                                                                                                          |
| DB_USER                | Name of the admin.                                                                                                                 |
| DB_PASSWORD            | Password of the admin.                                                                                                             |
| DB_HOST                | Hostname of the database.                                                                                                          |
| DB_PORT                | Port of the database.                                                                                                              |
| -                      | -                                                                                                                                  | 

