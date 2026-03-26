#!/bin/bash
# Helper: after terraform apply, push code to the EC2 instance and start services.
# Usage: ./deploy.sh <EC2_PUBLIC_IP> <SSH_KEY_PATH>
set -euo pipefail

IP="${1:?Usage: $0 <EC2_PUBLIC_IP> <SSH_KEY_PATH>}"
KEY="${2:?Usage: $0 <EC2_PUBLIC_IP> <SSH_KEY_PATH>}"
APP_DIR="/opt/health-tracker"

echo ">>> Syncing project to $IP:$APP_DIR ..."
rsync -avz --progress \
  -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  --exclude '.git' \
  --exclude 'MySql_Volume' \
  --exclude 'node_modules' \
  --exclude '.terraform' \
  --exclude '*.tfstate*' \
  --exclude '__pycache__' \
  --exclude '.env' \
  ../ "ec2-user@$IP:/tmp/health-tracker-src/"

echo ">>> Moving files into $APP_DIR and starting services ..."
ssh -i "$KEY" -o StrictHostKeyChecking=no "ec2-user@$IP" <<REMOTE
  sudo cp -r /tmp/health-tracker-src/* $APP_DIR/
  sudo chown -R ec2-user:ec2-user $APP_DIR
  cd $APP_DIR
  docker-compose up -d --build
REMOTE

echo ">>> Deploy complete. Frontend: http://$IP:3000  API: http://$IP:8000/docs"
