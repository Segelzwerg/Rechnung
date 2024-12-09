============
Installation
============

There are several ways to run this application yourself. Currently, we are only supporting a docker compose setup for
production.

Development
===========

We are using poetry as dependency management tool. After you have setup your environment, run ``poetry install`` in
the root directory of the project.

Docker Compose
==============

Create a new directory where you want to store the configuration files, e.g. ``rechnung``.
We are providing a `docker compose file <https://github.com/Segelzwerg/Rechnung/blob/main/compose.yaml>`_ as starter
which you can customize to your needs.
You have to options:

#. Build from source
#. Use prebuild image

Compose File
------------
We recommend to use the pre-built image:

.. code :: yaml

    services:
      rechnung:
        #build: . # Enable if you want to build from source
        image: ghcr.io/segelzwerg/segelzwerg/rechnung:latest

Next you can set the port exposure. The left side is how the application can be reached via docker and the right side
is the internal port which you must not change.

.. code :: yaml

    ports:
      - "12321:8000" # You can change to any port you like.

Do not change the ``depends_on``. Otherwise you will run into problems during the migration phase while starting the
webapp.

You have to set some environment variables. See the table below for more.

.. code :: yaml

    environment:
      - SECRET_KEY=$SECRET_KEY
      - ALLOWED_HOSTS=$ALLOWED_HOSTS
      - DB_NAME=$DB_NAME
      - DB_USER=$DB_USER
      - DB_PASSWORD=$DB_PASSWORD
      - DB_HOST=$DB_HOST
      - DB_PORT=$DB_PORT
      - DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

========================= =====
Env Var                   Value
========================= =====
DJANGO_SETTINGS_MODULE    The path to the django settings file you want to use. This should be ``rechnung.prod_settings`` if you don't require customizations.
ALLOWED_HOSTS             List of you hostname you want to access the application. E.g. `"['0.0.0.0']"`.
SECRET_KEY                Security string. Must not be shared.
DB_NAME                   Any name of the database.
DB_USER                   Name of the admin.
DB_PASSWORD               Password of the admin.
DB_HOST                   Hostname of the database. It must be the same as docker compose service.
DB_PORT                   Port of the database.
========================= =====

Finally, we require a database.

.. code :: yaml

  postgres:
    image: postgres:17
    volumes:
      #- <external_path>:/var/lib/postgresql/data/ # Enable if you want to use an external drive
      - /var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=$DB_USER
      - POSTGRES_PASSWORD=$DB_PASSWORD
      - POSTGRES_DB=$DB_NAME

Start Docker Compose
--------------------
After you created the above file, you can start the app with ``docker compose up``.