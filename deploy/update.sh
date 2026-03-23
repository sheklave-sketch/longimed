#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# LongiMed — Deploy / update script
# Run after every push:  bash /root/longimed/deploy/update.sh
# ─────────────────────────────────────────────────────────────────
set -e

APP_DIR="/root/longimed"
cd "$APP_DIR"

echo "==> Pulling latest code..."
git pull origin main

echo "==> Running database migrations..."
docker compose run --rm bot alembic upgrade head

echo "==> Rebuilding and restarting containers..."
docker compose up -d --build --remove-orphans

echo "==> Cleaning up old images..."
docker image prune -f

echo ""
echo "✅ Deployment complete!"
docker compose ps
