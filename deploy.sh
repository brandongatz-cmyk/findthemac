#!/bin/bash
# FindTheMac VPS Deployment Script
# Run this on your Hostinger VPS (Ubuntu 24.04)
# Usage: ssh root@2.24.76.74, then paste this script

set -e

echo "=== Step 1: System Update ==="
apt update && apt upgrade -y

echo "=== Step 2: Install Dependencies ==="
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git ufw

echo "=== Step 3: Firewall Setup ==="
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "=== Step 4: Clone the App ==="
mkdir -p /var/www
cd /var/www
git clone -b claude/apple-product-alerts-ST7Go https://github.com/brandongatz-cmyk/findthemac.git
cd findthemac

echo "=== Step 5: Python Virtual Environment ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Step 6: Create Environment File ==="
cat > /var/www/findthemac/.env << 'ENVFILE'
# Monitoring intervals (Free=15min, Pro=90sec, Ultra=15sec)
CHECK_INTERVAL_FREE_MINUTES=15
CHECK_INTERVAL_PRO_SECONDS=90
CHECK_INTERVAL_ULTRA_SECONDS=15

# Email alerts (Gmail example — use an App Password, not your real password)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=you@gmail.com
# SMTP_PASSWORD=your-app-password
# EMAIL_FROM=you@gmail.com

# SMS alerts (get these from twilio.com/console)
# TWILIO_ACCOUNT_SID=your-sid
# TWILIO_AUTH_TOKEN=your-token
# TWILIO_FROM_NUMBER=+1234567890

# Stripe (get these from dashboard.stripe.com)
# STRIPE_SECRET_KEY=sk_live_xxx
# STRIPE_PUBLISHABLE_KEY=pk_live_xxx
# STRIPE_PRICE_PRO=price_xxx
# STRIPE_PRICE_ULTRA=price_xxx

# Firebase Auth (get from console.firebase.google.com)
# FIREBASE_API_KEY=AIzaSy...
# FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
# FIREBASE_PROJECT_ID=your-project
# FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}
ENVFILE

echo "=== Step 7: Create systemd Service ==="
cat > /etc/systemd/system/findthemac.service << 'SERVICE'
[Unit]
Description=FindTheMac Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/findthemac
Environment="PATH=/var/www/findthemac/venv/bin"
EnvironmentFile=/var/www/findthemac/.env
ExecStart=/var/www/findthemac/venv/bin/gunicorn app:app --workers 2 --threads 4 --timeout 120 --bind 127.0.0.1:5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "=== Step 8: Set Permissions ==="
chown -R www-data:www-data /var/www/findthemac

echo "=== Step 9: Start the App ==="
systemctl daemon-reload
systemctl enable findthemac
systemctl start findthemac

echo "=== Step 10: Configure Nginx ==="
cat > /etc/nginx/sites-available/findthemac << 'NGINX'
server {
    listen 80;
    server_name findthemac.com www.findthemac.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/findthemac /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "=== Step 11: SSL Certificate ==="
echo "Run this AFTER your DNS is pointing to this server:"
echo "  certbot --nginx -d findthemac.com -d www.findthemac.com"

echo ""
echo "========================================="
echo "  FindTheMac is running!"
echo "  http://2.24.76.74 — test it now"
echo "  "
echo "  NEXT STEPS:"
echo "  1. Point findthemac.com DNS A record to 2.24.76.74"
echo "  2. Run: certbot --nginx -d findthemac.com -d www.findthemac.com"
echo "  3. Edit /var/www/findthemac/.env to add SMTP/Twilio keys"
echo "  4. Run: systemctl restart findthemac"
echo "========================================="
