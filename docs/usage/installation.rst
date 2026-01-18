============
Installation
============

There are several ways to run this application yourself. Currently, we are only supporting a docker compose setup for
production.

Development
===========

We are using uv as dependency management tool. After you have setup your environment, run ``uv sync`` in
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
We recommend to use the pre-built image. Use the ``latest`` tag for the stable release version and ``main`` for
current development branch. Use only ``latest`` for production environments.

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
      SECRET_KEY: $SECRET_KEY
      ALLOWED_HOSTS: $ALLOWED_HOSTS
      DATABASE_URL: "postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

========================= =====
Env Var                   Value
========================= =====
SECRET_KEY                Security string. Must not be shared.
ALLOWED_HOSTS             List of you hostname you want to access the application. E.g. `"['0.0.0.0']"`.
DATABASE_URL              Database URL.
CSRF_TRUSTED_ORIGINS      (Optional, Default: `http://*,https://*`) Used for endpoint names under which the server can be targeted. This is required for POST requests.
========================= =====

Finally, we require a database.

.. code :: yaml

  postgres:
    image: postgres:18
    volumes:
      #- <external_path>:/var/lib/postgresql/ # Enable if you want to use an external drive
      - /var/lib/postgresql/
    environment:
      POSTGRES_USER: $DB_USER
      POSTGRES_PASSWORD: $DB_PASSWORD
      # POSTGRES_PASSWORD_FILE: ... # For "docker secret"-like files
      POSTGRES_DB: $DB_NAME

Start Docker Compose
--------------------
After you created the above file, you can start the app with ``docker compose up``.

Proxmox
========
Setup a Ubuntu VM e.g. with by running

.. code :: shell

    bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/vm/ubuntu2504-vm.sh)"

on the pve shell.

Login to VM after creation and run:

.. code :: shell

    bash -c "$(curl -fsSL https://raw.githubusercontent.com/Segelzwerg/Rechnung/main/proxmox/setup.sh)"

Follow the instructions and enter the required secrets & passwords.