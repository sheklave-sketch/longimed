#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# LongiMed — One-time VPS setup script
# Run once on a fresh server as root:
#   bash setup_vps.sh
# ─────────────────────────────────────────────────────────────────
set -e

DOMAIN="longimed.yourdomain.com"   # ← change this
APP_DIR="/root/longimed"
REPO_URL="https://github.com/sheklave-sketch/longimed.git"

echo "==> Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

echo "==> Installing dependencies..."
apt-get install -y -qq \
    curl git nginx certbot python3-certbot-nginx \
    ufw fail2ban

# ── Docker ───────────────────────────────────────────────────────
echo "==> Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "    Docker already installed."
fi

# Docker Compose v2 (plugin)
if ! docker compose version &> /dev/null; then
    echo "==> Installing Docker Compose plugin..."
    apt-get install -y docker-compose-plugin
fi

# ── Firewall ─────────────────────────────────────────────────────
echo "==> Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ── Clone repo ───────────────────────────────────────────────────
echo "==> Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "    $APP_DIR already exists — skipping clone."
else
    git clone "$REPO_URL" "$APP_DIR"
fi

# ── Environment file ─────────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo "⚠️  .env created from .env.example."
    echo "    Edit it now: nano $APP_DIR/.env"
    echo "    Fill in: TELEGRAM_BOT_TOKEN, DATABASE_URL, OPENROUTER_API_KEY, etc."
fi

# ── Nginx config ─────────────────────────────────────────────────
echo "==> Writing nginx config..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/longimed
sed -i "s/longimed.yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/longimed
ln -sf /etc/nginx/sites-available/longimed /etc/nginx/sites-enabled/longimed
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── SSL ──────────────────────────────────────────────────────────
echo "==> Obtaining SSL certificate for $DOMAIN..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    --email admin@"$DOMAIN" --redirect || echo "⚠️  Certbot failed — run manually after DNS is set."

# ── Systemd service ──────────────────────────────────────────────
echo "==> Installing systemd service..."
cp "$APP_DIR/deploy/longimed.service" /etc/systemd/system/longimed.service
systemctl daemon-reload
systemctl enable longimed
systemctl start longimed

echo ""
echo "✅ Setup complete!"
echo "   Logs:    journalctl -u longimed -f"
echo "   Status:  systemctl status longimed"
echo "   Deploy:  bash $APP_DIR/deploy/update.sh"
