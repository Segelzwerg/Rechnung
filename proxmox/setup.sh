sudo apt update
sudo apt ugpgrade -y
# Add Docker's official GPG key:
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin postgresql -y
sudo systemctl start docker
sudo groupadd docker
sudo usermod -aG docker $USER
sudo systemctl restart docker
sudo systemctl start postgresql
sudo systemctl enable postgresql
read -p "Password for postgres super admin user: " postgres_password
read -p "Password for postgres service account: " service_postgres_password
read -p "Secret Key for the application: " secrect_key

# Use single quotes for the SQL command to avoid shell expansion issues with passwords
sudo -u postgres psql -c "ALTER USER postgres WITH ENCRYPTED PASSWORD '${postgres_password}';"
sudo -u postgres psql -c "DROP USER IF EXISTS rechnung_manager;"
sudo -u postgres psql -c "CREATE USER rechnung_manager WITH ENCRYPTED PASSWORD '${service_postgres_password}';"
sudo -u postgres psql -c "ALTER ROLE rechnung_manager SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS rechnung_db;"
sudo -u postgres psql -c "CREATE DATABASE rechnung_db OWNER rechnung_manager;"

# Update postgresql.conf to listen on all addresses
PG_CONF=$(find /etc/postgresql -name postgresql.conf)
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$PG_CONF"

# Update pg_hba.conf to allow connections from the docker network
PG_HBA=$(find /etc/postgresql -name pg_hba.conf)
# Use 'scram-sha-256' depending on your Postgres version, 'all' for the DB is safer for setup
echo "host    rechnung_db    rechnung_manager    0.0.0.0/0    scram-sha-256" | sudo tee -a "$PG_HBA"

sudo systemctl restart postgresql
ip_addresses=$(ip -4 -o addr show | awk '/inet/ {print $4}'| cut -d/ -f1 | paste -s -d, /dev/stdin)


# Create a .env file so docker compose can read it even with sudo
cat <<EOF > .env
ALLOWED_HOSTS=${ip_addresses}
DB_USER=rechnung_manager
DB_PASSWORD=${service_postgres_password}
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=rechnung_db
SECRET_KEY=${secrect_key}
EOF

wget https://raw.githubusercontent.com/Segelzwerg/Rechnung/refs/heads/proxmox-script/proxmox/compose.yaml

# Run docker compose; it will automatically pick up the .env file in the same directory
sudo docker compose up
