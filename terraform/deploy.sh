#!/bin/bash
# Helper: after terraform apply, push code to the EC2 instance and start services.
# Usage: ./deploy.sh <EC2_PUBLIC_IP> <SSH_KEY_PATH>
set -euo pipefail

IP="${1:?Usage: $0 <EC2_PUBLIC_IP> <SSH_KEY_PATH>}"
KEY="${2:?Usage: $0 <EC2_PUBLIC_IP> <SSH_KEY_PATH>}"
APP_DIR="/opt/health-tracker"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no"

echo ">>> Ensuring target directory exists on remote ..."
ssh $SSH_OPTS "ec2-user@$IP" "sudo mkdir -p $APP_DIR && sudo chown -R ec2-user:ec2-user $APP_DIR"

echo ">>> Syncing project to $IP:$APP_DIR ..."
rsync -avz --progress \
  -e "ssh $SSH_OPTS" \
  --exclude '.git' \
  --exclude 'MySql_Volume/' \
  --exclude 'node_modules/' \
  --exclude 'frontend/node_modules/' \
  --exclude '.terraform/' \
  --exclude '*.tfstate*' \
  --exclude '__pycache__/' \
  --exclude '.env' \
  --exclude 'terraform/' \
  --exclude 'uploads/' \
  --exclude '.cursor/' \
  --exclude '.streamlit/secrets.toml' \
  --exclude 'Agents/__pycache__/' \
  ../ "ec2-user@$IP:$APP_DIR/"

echo ">>> Starting services ..."
ssh $SSH_OPTS "ec2-user@$IP" "cd $APP_DIR && docker-compose up -d --build"

echo ">>> Deploy complete. Frontend: http://$IP:3000  API: http://$IP:8000/docs"
