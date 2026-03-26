#!/bin/bash
set -euo pipefail
exec > /var/log/user-data.log 2>&1

echo ">>> Starting Health Tracker bootstrap"

# -------------------------------------------------------------------
# 1. System packages
# -------------------------------------------------------------------
dnf update -y
dnf install -y docker git rsync

# -------------------------------------------------------------------
# 2. Docker, Docker Compose & Buildx (pinned versions for reliability)
# -------------------------------------------------------------------
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

COMPOSE_VERSION="v2.32.4"
curl -L "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

mkdir -p /usr/local/lib/docker/cli-plugins
BUILDX_VERSION="v0.21.1"
curl -L "https://github.com/docker/buildx/releases/download/$${BUILDX_VERSION}/buildx-$${BUILDX_VERSION}.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

# -------------------------------------------------------------------
# 3. Mount the EBS data volume
# -------------------------------------------------------------------
DATA_DEVICE="${ebs_device}"
DATA_MOUNT="${data_mount}"

# Wait for the EBS device to appear (can take a few seconds)
for i in $(seq 1 30); do
  [ -b "$DATA_DEVICE" ] && break
  echo "Waiting for $DATA_DEVICE ..."
  sleep 2
done

# Format only if no filesystem exists
if ! blkid "$DATA_DEVICE"; then
  mkfs.xfs "$DATA_DEVICE"
fi

mkdir -p "$DATA_MOUNT"
mount "$DATA_DEVICE" "$DATA_MOUNT"

# Persist across reboots
if ! grep -q "$DATA_DEVICE" /etc/fstab; then
  echo "$DATA_DEVICE  $DATA_MOUNT  xfs  defaults,nofail  0  2" >> /etc/fstab
fi

# Create sub-directories for persistent data
mkdir -p "$DATA_MOUNT/mysql"
mkdir -p "$DATA_MOUNT/uploads"
mkdir -p "$DATA_MOUNT/kafka-data"

# -------------------------------------------------------------------
# 4. Clone / update the repo
# -------------------------------------------------------------------
APP_DIR="/opt/health-tracker"
mkdir -p "$APP_DIR"

GITHUB_PAT="${github_pat}"
GITHUB_REPO="${github_repo}"
GITHUB_BRANCH="${github_branch}"

if [ -n "$GITHUB_PAT" ] && [ -n "$GITHUB_REPO" ]; then
  CLONE_URL="https://$${GITHUB_PAT}@github.com/$${GITHUB_REPO}.git"

  if [ -d "$APP_DIR/.git" ]; then
    echo ">>> Repo exists, pulling latest $GITHUB_BRANCH ..."
    cd "$APP_DIR"
    git fetch origin
    git reset --hard "origin/$GITHUB_BRANCH"
  else
    echo ">>> Cloning $GITHUB_REPO ($GITHUB_BRANCH) ..."
    git clone -b "$GITHUB_BRANCH" "$CLONE_URL" "$APP_DIR"
  fi

  # Wipe the PAT from git remote so it's not stored on disk
  cd "$APP_DIR"
  git remote set-url origin "https://github.com/$${GITHUB_REPO}.git"
else
  echo ">>> No GitHub PAT provided - skipping clone."
  echo ">>> Push code manually: deploy.sh or scp."
fi

cd "$APP_DIR"

# -------------------------------------------------------------------
# 5. Write .env with secrets from Terraform
# -------------------------------------------------------------------
cat > "$APP_DIR/.env" <<ENVFILE
OPENAI_API_KEY=${openai_api_key}
GROQ_API_KEY=${groq_api_key}
JWT_SECRET=${jwt_secret}
TRAINER_MODEL=gpt-4o-mini

# DB (also set in docker-compose environment, but available for scripts)
DB_HOST=mysql
DB_PORT=3306
DB_USER=user
DB_PASSWORD=${db_password}
DB_NAME=healthtracker

# Admin user seeded on startup
ADMIN_USERNAME=${admin_username}
ADMIN_PASSWORD=${admin_password}

# Kafka (internal docker network)
KAFKA_BOOTSTRAP_SERVER_DOCKER=kafka:29092
SCHEMA_REGISTRY_URL_DOCKER=http://schema-registry:8082
ENVFILE

# -------------------------------------------------------------------
# 6. Docker-compose override – point volumes to EBS mount
# -------------------------------------------------------------------
IMDS_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300" || true)
INSTANCE_PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $${IMDS_TOKEN}" http://169.254.169.254/latest/meta-data/public-ipv4 || echo "127.0.0.1")

cat > "$APP_DIR/docker-compose.override.yml" <<OVERRIDE
services:
  mysql:
    volumes:
      - ${data_mount}/mysql:/var/lib/mysql

  api:
    volumes:
      - ${data_mount}/uploads:/app/uploads

  kafka:
    environment:
      KAFKA_ADVERTISED_LISTENERS: >-
        PLAINTEXT://kafka:29092,PLAINTEXT_HOST://$${INSTANCE_PUBLIC_IP}:9092,PLAINTEXT_LOCAL://localhost:9093
    volumes:
      - ${data_mount}/kafka-data:/var/lib/kafka/data
OVERRIDE

# -------------------------------------------------------------------
# 7. Start services
# -------------------------------------------------------------------
chown -R ec2-user:ec2-user "$APP_DIR"

if [ -f "$APP_DIR/docker-compose.yml" ]; then
  cd "$APP_DIR"
  /usr/local/bin/docker-compose up -d --build
  echo ">>> All services started"
else
  echo ">>> docker-compose.yml not found at $APP_DIR"
  echo ">>> Push code manually, then run: cd $APP_DIR && docker-compose up -d --build"
fi

echo ">>> Bootstrap complete"
