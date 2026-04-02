#!/usr/bin/env python3
"""
FindTheMac — Apple Refurbished Product Alert Web Application.

A single-page web app that lets users browse Apple products and set up
email/SMS alerts for when those products appear on Apple's refurbished store.
"""

import json
import logging
import os
import re
import smtplib
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("findthemac")

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "findthemac.db")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))

# ============================================================================
# Apple product catalog
# ============================================================================
from products import CATEGORIES, PRODUCTS, get_product_by_id

# ============================================================================
# Database
# ============================================================================

def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def get_db_connection():
    """Context manager for use outside Flask request context."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                notify_email INTEGER DEFAULT 0,
                notify_sms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                notified_at TEXT,
                active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS refurbished_products (
                part_number TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                category TEXT,
                price TEXT,
                original_price TEXT,
                savings TEXT,
                first_seen TEXT,
                last_seen TEXT,
                available INTEGER DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_product ON alerts(product_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);
            CREATE INDEX IF NOT EXISTS idx_refurb_category ON refurbished_products(category);
        """)
        conn.commit()


# ============================================================================
# Apple Refurbished Scraper
# ============================================================================

REFURB_BASE = "https://www.apple.com/shop/refurbished"
REFURB_CATEGORIES = ["mac", "ipad", "iphone", "watch", "airpods", "appletv", "homepod"]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
BOOTSTRAP_RE = re.compile(
    r"window\.REFURB_GRID_BOOTSTRAP\s*=\s*(\{.*?\});\s*$",
    re.MULTILINE | re.DOTALL,
)


def scrape_refurbished_category(category):
    """Scrape a single refurbished category page and return product list."""
    url = f"{REFURB_BASE}/{category}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        match = BOOTSTRAP_RE.search(resp.text)
        if not match:
            return []
        data = json.loads(match.group(1))
        tiles = data.get("tiles", [])
        products = []
        for tile in tiles:
            price_info = tile.get("price", {})
            current = price_info.get("currentPrice", {})
            products.append({
                "part_number": tile.get("partNumber", ""),
                "title": tile.get("title", ""),
                "url": "https://www.apple.com" + tile.get("productDetailsUrl", ""),
                "category": category,
                "price": current.get("raw_amount", ""),
                "original_price": str(price_info.get("originalProductAmount", "")),
                "savings": price_info.get("savings", ""),
            })
        return [p for p in products if p["part_number"]]
    except Exception as exc:
        logger.error("Failed to scrape %s: %s", url, exc)
        return []


def scrape_all_refurbished():
    """Scrape all refurbished categories and return combined product list."""
    all_products = []
    for cat in REFURB_CATEGORIES:
        products = scrape_refurbished_category(cat)
        all_products.extend(products)
        time.sleep(1)  # Be polite
    logger.info("Scraped %d refurbished products total", len(all_products))
    return all_products


# ============================================================================
# Product matching — match catalog products to refurbished listings
# ============================================================================

def match_product_to_refurbished(product, refurbished_list):
    """Check if a catalog product has matching items in the refurbished store.

    Uses keyword matching: all keywords from the catalog product must appear
    in the refurbished listing title (case-insensitive).

    Returns list of matching refurbished products.
    """
    matches = []
    keywords = product.get("keywords", [])
    if not keywords:
        return matches

    for refurb in refurbished_list:
        title_lower = refurb["title"].lower()
        if all(kw.lower() in title_lower for kw in keywords):
            matches.append(refurb)

    return matches


# ============================================================================
# Notifications
# ============================================================================

def send_email_notification(to_email, product_name, refurb_matches):
    """Send an email alert about available refurbished products."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP not configured, skipping email to %s", to_email)
        return False

    subject = f"FindTheMac Alert: {product_name} is available refurbished!"

    # Build HTML
    rows = ""
    for m in refurb_matches[:10]:
        rows += f"""<tr>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <a href="{m['url']}" style="color:#0071e3;text-decoration:none;font-weight:600;">{m['title']}</a>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">
                <strong>${m['price']}</strong><br>
                <span style="color:#86868b;text-decoration:line-through;font-size:0.85em;">${m['original_price']}</span><br>
                <span style="color:#2d8a2d;font-size:0.85em;">{m['savings']}</span>
            </td>
        </tr>"""

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#f5f5f7;padding:20px;text-align:center;border-radius:12px 12px 0 0;">
            <h1 style="color:#1d1d1f;margin:0;font-size:22px;">FindTheMac</h1>
        </div>
        <div style="padding:24px;background:white;border:1px solid #e5e5e5;">
            <h2 style="color:#1d1d1f;font-size:18px;">Good news! {product_name} is available on Apple Refurbished.</h2>
            <p style="color:#86868b;">We found {len(refurb_matches)} matching listing(s):</p>
            <table style="width:100%;border-collapse:collapse;">{rows}</table>
            <p style="margin-top:20px;">
                <a href="https://www.apple.com/shop/refurbished" style="background:#0071e3;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
                    Shop Apple Refurbished
                </a>
            </p>
        </div>
        <div style="padding:16px;text-align:center;background:#f5f5f7;border-radius:0 0 12px 12px;">
            <p style="color:#86868b;font-size:12px;margin:0;">Sent by FindTheMac — Apple Refurbished Product Monitor</p>
        </div>
    </div>"""

    text = f"FindTheMac Alert: {product_name} is available refurbished!\n\n"
    for m in refurb_matches[:10]:
        text += f"- {m['title']} — ${m['price']} (was ${m['original_price']})\n  {m['url']}\n\n"
    text += "Shop: https://www.apple.com/shop/refurbished\n"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_email], msg.as_string())
        logger.info("Email sent to %s for %s", to_email, product_name)
        return True
    except Exception as exc:
        logger.error("Email failed to %s: %s", to_email, exc)
        return False


def send_sms_notification(to_phone, product_name, refurb_matches):
    """Send an SMS alert via Twilio."""
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_num = os.getenv("TWILIO_FROM_NUMBER", "")

    if not sid or not token or not from_num:
        logger.warning("Twilio not configured, skipping SMS to %s", to_phone)
        return False

    body = f"FindTheMac: {product_name} is now on Apple Refurbished!\n"
    for m in refurb_matches[:2]:
        body += f"\n${m['price']} - {m['title'][:50]}"
    body += f"\n\n{len(refurb_matches)} listing(s) at apple.com/shop/refurbished"

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(body=body, from_=from_num, to=to_phone)
        logger.info("SMS sent to %s for %s", to_phone, product_name)
        return True
    except Exception as exc:
        logger.error("SMS failed to %s: %s", to_phone, exc)
        return False


# ============================================================================
# Background monitor
# ============================================================================

def check_and_notify():
    """Main check loop: scrape refurbished store, match against active alerts, notify."""
    logger.info("Running refurbished availability check...")

    refurbished = scrape_all_refurbished()
    if not refurbished:
        logger.warning("No refurbished products found — skipping this cycle.")
        return

    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        # Update refurbished products table
        current_parts = set()
        for p in refurbished:
            current_parts.add(p["part_number"])
            existing = conn.execute(
                "SELECT part_number FROM refurbished_products WHERE part_number = ?",
                (p["part_number"],),
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE refurbished_products
                    SET title=?, url=?, price=?, original_price=?, savings=?, last_seen=?, available=1
                    WHERE part_number=?
                """, (p["title"], p["url"], p["price"], p["original_price"], p["savings"], now, p["part_number"]))
            else:
                conn.execute("""
                    INSERT INTO refurbished_products (part_number, title, url, category, price, original_price, savings, first_seen, last_seen, available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (p["part_number"], p["title"], p["url"], p["category"], p["price"], p["original_price"], p["savings"], now, now))

        # Mark missing products as unavailable
        conn.execute(
            "UPDATE refurbished_products SET available = 0 WHERE part_number NOT IN ({})".format(
                ",".join("?" * len(current_parts))
            ),
            list(current_parts),
        )
        conn.commit()

        # Process active alerts
        alerts = conn.execute(
            "SELECT * FROM alerts WHERE active = 1"
        ).fetchall()

        for alert in alerts:
            product = get_product_by_id(alert["product_id"])
            if not product:
                continue

            matches = match_product_to_refurbished(product, refurbished)
            if not matches:
                continue

            # Found matches — notify!
            logger.info("Product '%s' has %d refurbished match(es)", product["name"], len(matches))

            sent = False
            if alert["notify_email"] and alert["email"]:
                sent = send_email_notification(alert["email"], product["name"], matches) or sent
            if alert["notify_sms"] and alert["phone"]:
                sent = send_sms_notification(alert["phone"], product["name"], matches) or sent

            if sent:
                conn.execute(
                    "UPDATE alerts SET notified_at = ?, active = 0 WHERE id = ?",
                    (now, alert["id"]),
                )

        conn.commit()

    logger.info("Check complete.")


def background_monitor():
    """Background thread that periodically checks for refurbished products."""
    # Wait a bit before first check to let the app start up
    time.sleep(10)
    while True:
        try:
            check_and_notify()
        except Exception as exc:
            logger.error("Monitor error: %s", exc)
        time.sleep(CHECK_INTERVAL * 60)


# ============================================================================
# API Routes
# ============================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/products")
def api_products():
    """Return the full product catalog."""
    return jsonify({"products": PRODUCTS, "categories": CATEGORIES})


@app.route("/api/refurbished/status/<product_id>")
def api_refurbished_status(product_id):
    """Check if a product currently has refurbished listings."""
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db = get_db()
    # Get all available refurbished products in this category
    refurbished = db.execute(
        "SELECT * FROM refurbished_products WHERE category = ? AND available = 1",
        (product["category"],),
    ).fetchall()

    matches = match_product_to_refurbished(product, [dict(r) for r in refurbished])

    return jsonify({
        "product_id": product_id,
        "available": len(matches) > 0,
        "count": len(matches),
        "listings": [dict(m) for m in matches[:20]],
    })


@app.route("/api/alerts", methods=["POST"])
def api_create_alert():
    """Create a new alert subscription."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    product_id = data.get("product_id", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    notify_email = bool(data.get("notify_email", False))
    notify_sms = bool(data.get("notify_sms", False))

    # Validation
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    if not notify_email and not notify_sms:
        return jsonify({"error": "Select at least one notification method"}), 400
    if notify_email and not email:
        return jsonify({"error": "Email address required"}), 400
    if notify_sms and not phone:
        return jsonify({"error": "Phone number required"}), 400
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email address"}), 400

    now = datetime.now(timezone.utc).isoformat()

    db = get_db()

    # Check if product is currently available on refurbished store
    refurbished = db.execute(
        "SELECT * FROM refurbished_products WHERE category = ? AND available = 1",
        (product["category"],),
    ).fetchall()
    matches = match_product_to_refurbished(product, [dict(r) for r in refurbished])

    if matches:
        # Product is available NOW — notify immediately and create a completed alert
        db.execute("""
            INSERT INTO alerts (product_id, email, phone, notify_email, notify_sms, created_at, notified_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (product_id, email, phone, int(notify_email), int(notify_sms), now, now))
        db.commit()

        # Send immediate notifications in background
        def _notify():
            if notify_email and email:
                send_email_notification(email, product["name"], matches)
            if notify_sms and phone:
                send_sms_notification(phone, product["name"], matches)

        threading.Thread(target=_notify, daemon=True).start()

        return jsonify({
            "status": "available_now",
            "message": f"{product['name']} is available now! Sending notification...",
            "count": len(matches),
            "listings": [dict(m) for m in matches[:10]],
        })

    else:
        # Product not available — create active alert
        db.execute("""
            INSERT INTO alerts (product_id, email, phone, notify_email, notify_sms, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (product_id, email, phone, int(notify_email), int(notify_sms), now))
        db.commit()

        return jsonify({
            "status": "watching",
            "message": f"Alert set! We'll notify you when {product['name']} appears on Apple Refurbished.",
        })


@app.route("/api/alerts/check", methods=["GET"])
def api_check_alerts():
    """Get count of active alert subscriptions (for admin/debugging)."""
    db = get_db()
    active = db.execute("SELECT COUNT(*) as cnt FROM alerts WHERE active = 1").fetchone()["cnt"]
    total = db.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()["cnt"]
    return jsonify({"active_alerts": active, "total_alerts": total})


@app.route("/api/refurbished/summary")
def api_refurbished_summary():
    """Get a summary of currently available refurbished products by category."""
    db = get_db()
    rows = db.execute("""
        SELECT category, COUNT(*) as count
        FROM refurbished_products
        WHERE available = 1
        GROUP BY category
    """).fetchall()
    summary = {r["category"]: r["count"] for r in rows}
    total = sum(summary.values())
    return jsonify({"categories": summary, "total": total})


# ============================================================================
# Startup
# ============================================================================

init_db()

# Start background monitor thread
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
