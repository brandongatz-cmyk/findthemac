#!/usr/bin/env python3
"""
FindTheMac — Apple Product Availability Alert Web Application.

A single-page web app that lets users browse Apple products and set up
email/SMS alerts for when those products become available on the Apple Store
(both new and refurbished).
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

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

import requests
import stripe
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
CHECK_INTERVAL_FREE = int(os.getenv("CHECK_INTERVAL_FREE_MINUTES", "15"))
CHECK_INTERVAL_PRO = int(os.getenv("CHECK_INTERVAL_PRO_SECONDS", "90"))
CHECK_INTERVAL_ULTRA = int(os.getenv("CHECK_INTERVAL_ULTRA_SECONDS", "15"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_ULTRA = os.getenv("STRIPE_PRICE_ULTRA", "")

try:
    import firebase_admin
    from firebase_admin import credentials as fb_credentials, auth as firebase_auth
    _fb_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
    if _fb_creds_json:
        firebase_admin.initialize_app(
            fb_credentials.Certificate(json.loads(_fb_creds_json))
        )
        FIREBASE_AVAILABLE = True
    else:
        FIREBASE_AVAILABLE = False
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.info("firebase-admin not installed — auth features disabled")

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
                tier TEXT DEFAULT 'free',
                check_new INTEGER DEFAULT 1,
                check_refurbished INTEGER DEFAULT 1,
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

            CREATE TABLE IF NOT EXISTS new_products (
                part_number TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                category TEXT,
                price TEXT,
                buyable INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_product ON alerts(product_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);
            CREATE INDEX IF NOT EXISTS idx_refurb_category ON refurbished_products(category);
            CREATE INDEX IF NOT EXISTS idx_new_category ON new_products(category);
            CREATE INDEX IF NOT EXISTS idx_new_buyable ON new_products(buyable);

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firebase_uid TEXT UNIQUE NOT NULL,
                email TEXT,
                display_name TEXT,
                phone TEXT,
                provider TEXT,
                stripe_customer_id TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_users_firebase ON users(firebase_uid);

            CREATE TABLE IF NOT EXISTS retailer_cache (
                cache_key TEXT PRIMARY KEY,
                retailer TEXT NOT NULL,
                product_id TEXT NOT NULL,
                data TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_retailer_cache_product ON retailer_cache(product_id);
        """)
        # Migration for existing databases
        for col, default in [("check_new", "1"), ("check_refurbished", "1")]:
            try:
                conn.execute(f"ALTER TABLE alerts ADD COLUMN {col} INTEGER DEFAULT {default}")
            except sqlite3.OperationalError:
                pass
        for col in ["stripe_customer_id", "stripe_subscription_id", "user_id"]:
            try:
                conn.execute(f"ALTER TABLE alerts ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass
        conn.commit()


# ============================================================================
# Shared HTTP headers
# ============================================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

http_session = requests.Session()
http_session.headers.update(HEADERS)

# ============================================================================
# Apple Refurbished Scraper
# ============================================================================

REFURB_BASE = "https://www.apple.com/shop/refurbished"
REFURB_CATEGORIES = ["mac", "ipad", "iphone", "watch", "airpods", "appletv", "homepod"]
BOOTSTRAP_RE = re.compile(
    r"window\.REFURB_GRID_BOOTSTRAP\s*=\s*(\{.*?\});\s*$",
    re.MULTILINE | re.DOTALL,
)


def scrape_refurbished_category(category):
    url = f"{REFURB_BASE}/{category}"
    try:
        resp = http_session.get(url, timeout=10)
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
    all_products = []
    for cat in REFURB_CATEGORIES:
        products = scrape_refurbished_category(cat)
        all_products.extend(products)
        time.sleep(1)
    logger.info("Scraped %d refurbished products total", len(all_products))
    return all_products


# ============================================================================
# Apple New Product Store Checker
# ============================================================================

BUY_PAGES = {
    "mac": [
        {"url": "https://www.apple.com/shop/buy-mac/macbook-air", "label": "MacBook Air"},
        {"url": "https://www.apple.com/shop/buy-mac/macbook-pro", "label": "MacBook Pro"},
        {"url": "https://www.apple.com/shop/buy-mac/imac", "label": "iMac"},
        {"url": "https://www.apple.com/shop/buy-mac/mac-mini", "label": "Mac mini"},
        {"url": "https://www.apple.com/shop/buy-mac/mac-studio", "label": "Mac Studio"},
        {"url": "https://www.apple.com/shop/buy-mac/mac-pro", "label": "Mac Pro"},
    ],
    "ipad": [
        {"url": "https://www.apple.com/shop/buy-ipad", "label": "iPad"},
        {"url": "https://www.apple.com/shop/buy-ipad/ipad-mini", "label": "iPad mini"},
        {"url": "https://www.apple.com/shop/buy-ipad/ipad-air", "label": "iPad Air"},
        {"url": "https://www.apple.com/shop/buy-ipad/ipad-pro", "label": "iPad Pro"},
    ],
    "iphone": [
        {"url": "https://www.apple.com/shop/buy-iphone", "label": "iPhone"},
    ],
    "watch": [
        {"url": "https://www.apple.com/shop/buy-watch", "label": "Apple Watch"},
    ],
    "airpods": [
        {"url": "https://www.apple.com/shop/buy-airpods", "label": "AirPods"},
    ],
    "appletv": [
        {"url": "https://www.apple.com/shop/buy-tv/apple-tv-4k", "label": "Apple TV"},
    ],
    "homepod": [
        {"url": "https://www.apple.com/shop/buy-homepod", "label": "HomePod"},
    ],
}

PART_NUMBER_RE = re.compile(r"[A-Z][A-Z0-9]{2,5}LL/A")


def scrape_buy_page(url, category, label):
    """Scrape an Apple buy page for part numbers and product info."""
    products = []
    try:
        resp = http_session.get(url, timeout=10)
        resp.raise_for_status()
        html = resp.text

        part_numbers = set(PART_NUMBER_RE.findall(html))

        page_title = label
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html)
        if title_match:
            clean = title_match.group(1).strip().replace("Buy ", "").replace(" - Apple", "").strip()
            if clean:
                page_title = clean

        for pn in part_numbers:
            products.append({
                "part_number": pn,
                "title": page_title,
                "url": url,
                "category": category,
            })

    except Exception as exc:
        logger.error("Failed to scrape buy page %s: %s", url, exc)

    return products


def check_buyability(part_numbers):
    """Check which part numbers are currently buyable via Apple's API."""
    results = {}
    pn_list = list(part_numbers)
    batch_size = 5

    for i in range(0, len(pn_list), batch_size):
        batch = pn_list[i:i + batch_size]
        params = {f"parts.{j}": pn for j, pn in enumerate(batch)}

        try:
            resp = http_session.get(
                "https://www.apple.com/shop/buyability-message",
                params=params,
                headers={"Accept": "application/json"},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                body = data.get("body", {})
                content = body.get("content", {})
                for pn in batch:
                    pn_data = content.get(pn, {})
                    results[pn] = pn_data.get("isBuyable", False)
            else:
                for pn in batch:
                    results[pn] = False
        except Exception as exc:
            logger.error("Buyability check failed: %s", exc)
            for pn in batch:
                results[pn] = False

        time.sleep(0.5)

    return results


def update_new_products_cache():
    """Scrape Apple Store buy pages and check availability of new products."""
    all_products = []

    for category, pages in BUY_PAGES.items():
        for page in pages:
            products = scrape_buy_page(page["url"], category, page["label"])
            all_products.extend(products)
            time.sleep(1)

    if not all_products:
        logger.warning("No new product part numbers found — skipping cache update.")
        return None

    part_numbers = [p["part_number"] for p in all_products]
    buyability = check_buyability(part_numbers)

    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        conn.execute("UPDATE new_products SET buyable = 0")

        for p in all_products:
            pn = p["part_number"]
            is_buyable = buyability.get(pn, False)
            existing = conn.execute(
                "SELECT part_number FROM new_products WHERE part_number = ?", (pn,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE new_products SET title=?, url=?, buyable=?, last_seen=?
                    WHERE part_number=?
                """, (p["title"], p["url"], int(is_buyable), now, pn))
            else:
                conn.execute("""
                    INSERT INTO new_products (part_number, title, url, category, buyable, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (pn, p["title"], p["url"], p["category"], int(is_buyable), now, now))

        conn.commit()

    buyable_count = sum(1 for v in buyability.values() if v)
    logger.info("Updated %d new products (%d buyable)", len(all_products), buyable_count)
    return all_products


# ============================================================================
# Third-Party Retailer Search (Best Buy, B&H Photo, Swappa)
# ============================================================================

RETAILER_CACHE_TTL = 300  # 5 minutes


def build_search_query(product, memory=None):
    """Build a search query string from product keywords and optional memory filter."""
    keywords = product.get("keywords", [])
    query = " ".join(keywords)
    if memory:
        query += f" {memory}GB"
    return query


def search_bestbuy(query):
    """Search Best Buy for products matching the query."""
    search_url = f"https://www.bestbuy.com/site/searchpage.jsp?st={quote_plus(query)}"
    try:
        resp = http_session.get(search_url, timeout=5)
        if resp.status_code != 200:
            return {"search_url": search_url, "listings": []}

        products = []
        sku_title_re = re.compile(
            r'class="sku-title"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        price_re = re.compile(r'"currentPrice":([\d.]+)')

        titles = sku_title_re.findall(resp.text)
        prices = price_re.findall(resp.text)

        for i, (url, title) in enumerate(titles[:10]):
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            price = prices[i] if i < len(prices) else ""
            if clean_title and "apple" in clean_title.lower():
                full_url = "https://www.bestbuy.com" + url if url.startswith("/") else url
                products.append({
                    "title": clean_title,
                    "price": price,
                    "url": full_url,
                    "condition": "new",
                })

        return {"search_url": search_url, "listings": products[:10]}
    except Exception as exc:
        logger.error("Best Buy search failed for '%s': %s", query, exc)
        return {"search_url": search_url, "listings": []}


def search_bh(query):
    """Search B&H Photo for products matching the query."""
    search_url = f"https://www.bhphotovideo.com/c/search?q={quote_plus(query)}&filters=fct_brand_name%3Aapple"
    try:
        resp = http_session.get(search_url, timeout=5)
        if resp.status_code != 200:
            return {"search_url": search_url, "listings": []}

        products = []
        ld_re = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
        for m in ld_re.finditer(resp.text):
            try:
                ld_data = json.loads(m.group(1))
                items = ld_data if isinstance(ld_data, list) else [ld_data]
                for item in items:
                    if item.get("@type") in ("Product", "IndividualProduct"):
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        products.append({
                            "title": item.get("name", ""),
                            "price": str(offers.get("price", "")),
                            "url": item.get("url", search_url),
                            "condition": "new",
                        })
            except (json.JSONDecodeError, TypeError, IndexError):
                pass

        # Fallback: regex for product tiles
        if not products:
            tile_re = re.compile(
                r'data-selenium="miniProductPage[^"]*Name"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
                r'data-selenium="miniProductPage[^"]*Price"[^>]*>\$?([\d,]+\.?\d*)',
                re.DOTALL,
            )
            for match in tile_re.finditer(resp.text):
                url, title, price = match.groups()
                clean_title = re.sub(r"<[^>]+>", "", title).strip()
                if clean_title:
                    full_url = "https://www.bhphotovideo.com" + url if url.startswith("/") else url
                    products.append({
                        "title": clean_title,
                        "price": price.replace(",", ""),
                        "url": full_url,
                        "condition": "new",
                    })

        return {"search_url": search_url, "listings": products[:10]}
    except Exception as exc:
        logger.error("B&H search failed for '%s': %s", query, exc)
        return {"search_url": search_url, "listings": []}


def search_swappa(query):
    """Search Swappa for used/refurbished products matching the query."""
    search_url = f"https://swappa.com/search?q={quote_plus(query)}"
    try:
        resp = http_session.get(search_url, timeout=5)
        if resp.status_code != 200:
            return {"search_url": search_url, "listings": []}

        products = []
        listing_re = re.compile(
            r'<a[^>]*href="(/listing/[^"]*)"[^>]*>.*?'
            r'<(?:h[2-6]|div|span)[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</(?:h[2-6]|div|span)>.*?'
            r'\$\s*([\d,]+\.?\d*)',
            re.DOTALL,
        )
        for match in listing_re.finditer(resp.text):
            url, title, price = match.groups()
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            if clean_title:
                products.append({
                    "title": clean_title,
                    "price": price.replace(",", ""),
                    "url": "https://swappa.com" + url,
                    "condition": "used",
                })

        # Also try JSON-LD
        if not products:
            ld_re = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
            for m in ld_re.finditer(resp.text):
                try:
                    ld_data = json.loads(m.group(1))
                    items = ld_data if isinstance(ld_data, list) else [ld_data]
                    for item in items:
                        if item.get("@type") in ("Product", "IndividualProduct", "Offer"):
                            offers = item.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            products.append({
                                "title": item.get("name", ""),
                                "price": str(offers.get("price", "")),
                                "url": item.get("url", search_url),
                                "condition": "used",
                            })
                except (json.JSONDecodeError, TypeError, IndexError):
                    pass

        return {"search_url": search_url, "listings": products[:10]}
    except Exception as exc:
        logger.error("Swappa search failed for '%s': %s", query, exc)
        return {"search_url": search_url, "listings": []}


def get_cached_retailer(product_id, retailer):
    """Get cached retailer results if still fresh."""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM retailer_cache WHERE cache_key = ?",
                (f"{retailer}:{product_id}",),
            ).fetchone()
            if row:
                fetched = datetime.fromisoformat(row["fetched_at"])
                age = (datetime.now(timezone.utc) - fetched).total_seconds()
                if age < RETAILER_CACHE_TTL:
                    return json.loads(row["data"])
    except Exception:
        pass
    return None


def cache_retailer_result(product_id, retailer, data):
    """Cache retailer search results."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO retailer_cache (cache_key, retailer, product_id, data, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (f"{retailer}:{product_id}", retailer, product_id, json.dumps(data), now))
            conn.commit()
    except Exception as exc:
        logger.error("Failed to cache retailer result: %s", exc)


def search_all_retailers(product, memory=None):
    """Search all third-party retailers for a product. Returns dict of results."""
    query = build_search_query(product, memory)
    product_id = product["id"]
    cache_suffix = f":{memory}" if memory else ""

    results = {}
    retailers = {
        "bestbuy": search_bestbuy,
        "bh": search_bh,
        "swappa": search_swappa,
    }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for name, fn in retailers.items():
            cached = get_cached_retailer(product_id + cache_suffix, name)
            if cached:
                results[name] = cached
            else:
                futures[executor.submit(fn, query)] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results[name] = result
                cache_retailer_result(product_id + cache_suffix, name, result)
            except Exception as exc:
                logger.error("Retailer %s search failed: %s", name, exc)
                results[name] = {"search_url": "", "listings": []}

    return results


# ============================================================================
# Product matching
# ============================================================================

def match_product_to_refurbished(product, refurbished_list):
    """Match a catalog product to refurbished listings using keyword matching."""
    matches = []
    keywords = product.get("keywords", [])
    if not keywords:
        return matches

    for refurb in refurbished_list:
        title_lower = refurb["title"].lower()
        if all(kw.lower() in title_lower for kw in keywords):
            matches.append(refurb)

    return matches


def match_product_to_new(product, new_products_list):
    """Match a catalog product to new Apple Store listings.

    Matches based on product subcategory against the buy page label.
    """
    matches = []
    subcategory = product.get("subcategory", "").lower()
    if not subcategory:
        return matches

    for item in new_products_list:
        item_label = item["title"].lower() if isinstance(item, dict) else item[1].lower()
        title = item_label
        if subcategory == title or subcategory.startswith(title) or title.startswith(subcategory):
            matches.append(item)

    return matches


# ============================================================================
# Notifications
# ============================================================================

def send_email_notification(to_email, product_name, refurb_matches, new_matches, retailer_results=None):
    """Send an email alert about available products across all sources."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP not configured, skipping email to %s", to_email)
        return False

    if retailer_results is None:
        retailer_results = {}

    avail_types = []
    if new_matches:
        avail_types.append("new")
    if refurb_matches:
        avail_types.append("refurbished")
    for rname, rdata in retailer_results.items():
        if rdata.get("listings"):
            label = {"bestbuy": "Best Buy", "bh": "B&H Photo", "swappa": "Swappa"}.get(rname, rname)
            avail_types.append(label)
    avail_label = ", ".join(avail_types) if avail_types else "multiple sources"

    subject = f"FindTheMac Alert: {product_name} is available!"

    # Build HTML sections
    new_section = ""
    if new_matches:
        seen_urls = set()
        unique_new = []
        for m in new_matches:
            url = m["url"] if isinstance(m, dict) else m[2]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_new.append(m)

        new_rows = ""
        for m in unique_new[:5]:
            title = m["title"] if isinstance(m, dict) else m[1]
            url = m["url"] if isinstance(m, dict) else m[2]
            new_rows += f"""<tr>
                <td style="padding:10px;border-bottom:1px solid #d0e4f5;">
                    <a href="{url}" style="color:#0071e3;text-decoration:none;font-weight:600;">{title}</a>
                </td>
                <td style="padding:10px;border-bottom:1px solid #d0e4f5;text-align:right;">
                    <span style="color:#0071e3;font-weight:600;">Buy New</span>
                </td>
            </tr>"""
        new_section = f"""
        <div style="background:#e3f2fd;border:1px solid #90caf9;border-radius:12px;padding:16px;margin-bottom:20px;">
            <h3 style="color:#1565c0;margin:0 0 10px;font-size:16px;">Available NEW on Apple.com</h3>
            <table style="width:100%;border-collapse:collapse;">{new_rows}</table>
        </div>"""

    refurb_section = ""
    if refurb_matches:
        refurb_rows = ""
        for m in refurb_matches[:10]:
            refurb_rows += f"""<tr>
                <td style="padding:10px;border-bottom:1px solid #c8e6c9;">
                    <a href="{m['url']}" style="color:#0071e3;text-decoration:none;font-weight:600;">{m['title']}</a>
                </td>
                <td style="padding:10px;border-bottom:1px solid #c8e6c9;text-align:right;">
                    <strong>${m['price']}</strong><br>
                    <span style="color:#86868b;text-decoration:line-through;font-size:0.85em;">${m['original_price']}</span><br>
                    <span style="color:#2d8a2d;font-size:0.85em;">{m['savings']}</span>
                </td>
            </tr>"""
        refurb_section = f"""
        <div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:12px;padding:16px;margin-bottom:20px;">
            <h3 style="color:#2d8a2d;margin:0 0 10px;font-size:16px;">Available on Apple Refurbished ({len(refurb_matches)} listing{'s' if len(refurb_matches) != 1 else ''})</h3>
            <table style="width:100%;border-collapse:collapse;">{refurb_rows}</table>
        </div>"""

    retailer_section = ""
    retailer_configs = {
        "bestbuy": {"name": "Best Buy", "bg": "#fff8e1", "border": "#ffe082", "color": "#f57f17"},
        "bh": {"name": "B&H Photo", "bg": "#fce4ec", "border": "#f48fb1", "color": "#c62828"},
        "swappa": {"name": "Swappa", "bg": "#f3e5f5", "border": "#ce93d8", "color": "#6a1b9a"},
    }
    for rname, cfg in retailer_configs.items():
        rdata = retailer_results.get(rname, {})
        listings = rdata.get("listings", [])
        if listings:
            rows = ""
            for item in listings[:5]:
                url = item.get("url", "")
                title = item.get("title", "Unknown")
                price = item.get("price", "")
                price_display = f"${price}" if price else "See Price"
                rows += f"""<tr>
                    <td style="padding:10px;border-bottom:1px solid {cfg['border']};">
                        <a href="{url}" style="color:#0071e3;text-decoration:none;font-weight:600;">{title}</a>
                    </td>
                    <td style="padding:10px;border-bottom:1px solid {cfg['border']};text-align:right;">
                        <strong>{price_display}</strong>
                    </td>
                </tr>"""
            retailer_section += f"""
            <div style="background:{cfg['bg']};border:1px solid {cfg['border']};border-radius:12px;padding:16px;margin-bottom:20px;">
                <h3 style="color:{cfg['color']};margin:0 0 10px;font-size:16px;">Available at {cfg['name']} ({len(listings)} listing{'s' if len(listings) != 1 else ''})</h3>
                <table style="width:100%;border-collapse:collapse;">{rows}</table>
            </div>"""

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#f5f5f7;padding:20px;text-align:center;border-radius:12px 12px 0 0;">
            <h1 style="color:#1d1d1f;margin:0;font-size:22px;">FindTheMac</h1>
        </div>
        <div style="padding:24px;background:white;border:1px solid #e5e5e5;">
            <h2 style="color:#1d1d1f;font-size:18px;">Good news! {product_name} is available.</h2>
            {new_section}
            {refurb_section}
            {retailer_section}
            <p style="margin-top:20px;">
                <a href="https://www.apple.com/shop" style="background:#0071e3;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
                    Shop Apple Store
                </a>
            </p>
        </div>
        <div style="padding:16px;text-align:center;background:#f5f5f7;border-radius:0 0 12px 12px;">
            <p style="color:#86868b;font-size:12px;margin:0;">Sent by FindTheMac — Apple Product Availability Monitor</p>
        </div>
    </div>"""

    text = f"FindTheMac Alert: {product_name} is available!\n\n"
    if new_matches:
        text += "AVAILABLE NEW ON APPLE.COM:\n"
        seen = set()
        for m in new_matches[:5]:
            url = m["url"] if isinstance(m, dict) else m[2]
            title = m["title"] if isinstance(m, dict) else m[1]
            if url not in seen:
                seen.add(url)
                text += f"- {title}: {url}\n"
        text += "\n"
    if refurb_matches:
        text += "AVAILABLE REFURBISHED:\n"
        for m in refurb_matches[:10]:
            text += f"- {m['title']} — ${m['price']} (was ${m['original_price']})\n  {m['url']}\n"
        text += "\n"
    for rname, rdata in retailer_results.items():
        listings = rdata.get("listings", [])
        if listings:
            label = {"bestbuy": "BEST BUY", "bh": "B&H PHOTO", "swappa": "SWAPPA"}.get(rname, rname.upper())
            text += f"AVAILABLE AT {label}:\n"
            for item in listings[:5]:
                title = item.get("title", "Unknown")
                url = item.get("url", "")
                price = item.get("price", "")
                text += f"- {title}" + (f" — ${price}" if price else "") + f"\n  {url}\n"
            text += "\n"
    text += "Shop: https://www.apple.com/shop\n"

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


def send_sms_notification(to_phone, product_name, refurb_matches, new_matches, retailer_results=None):
    """Send an SMS alert via Twilio with direct links."""
    if retailer_results is None:
        retailer_results = {}

    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_num = os.getenv("TWILIO_FROM_NUMBER", "")

    if not sid or not token or not from_num:
        logger.warning("Twilio not configured, skipping SMS to %s", to_phone)
        return False

    body = f"FindTheMac: {product_name} is now available!\n"
    if new_matches:
        url = new_matches[0]["url"] if isinstance(new_matches[0], dict) else new_matches[0][2]
        body += f"\nNEW on Apple.com:\n{url}"
    if refurb_matches:
        body += f"\nREFURBISHED ({len(refurb_matches)}):\n{refurb_matches[0]['url']}"
    for rname, rdata in retailer_results.items():
        listings = rdata.get("listings", [])
        if listings:
            label = {"bestbuy": "Best Buy", "bh": "B&H Photo", "swappa": "Swappa"}.get(rname, rname)
            url = listings[0].get("url", rdata.get("search_url", ""))
            body += f"\n{label}:\n{url}"

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

def update_refurbished_cache():
    refurbished = scrape_all_refurbished()
    if not refurbished:
        logger.warning("No refurbished products found — skipping this cycle.")
        return None

    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
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

        if current_parts:
            conn.execute(
                "UPDATE refurbished_products SET available = 0 WHERE part_number NOT IN ({})".format(
                    ",".join("?" * len(current_parts))
                ),
                list(current_parts),
            )
        conn.commit()

    return refurbished


def process_alerts(tier, refurbished, new_products):
    """Check active alerts for a given tier and send notifications for matches."""
    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        alerts = conn.execute(
            "SELECT * FROM alerts WHERE active = 1 AND tier = ?", (tier,)
        ).fetchall()

        if not alerts:
            return

        logger.info("Processing %d active '%s' tier alert(s)", len(alerts), tier)

        for alert in alerts:
            product = get_product_by_id(alert["product_id"])
            if not product:
                continue

            refurb_matches = match_product_to_refurbished(product, refurbished) if refurbished else []
            new_matches = match_product_to_new(product, new_products) if new_products else []

            retailer_results = search_all_retailers(product)
            has_retailer_hits = any(
                rdata.get("listings") for rdata in retailer_results.values()
            )

            if not refurb_matches and not new_matches and not has_retailer_hits:
                continue

            retailer_count = sum(len(d.get("listings", [])) for d in retailer_results.values())
            logger.info(
                "Product '%s': %d new + %d refurb + %d retailer [%s tier]",
                product["name"], len(new_matches), len(refurb_matches), retailer_count, tier,
            )

            sent = False
            if alert["notify_email"] and alert["email"]:
                sent = send_email_notification(
                    alert["email"], product["name"], refurb_matches, new_matches, retailer_results
                ) or sent
            if alert["notify_sms"] and alert["phone"]:
                sent = send_sms_notification(
                    alert["phone"], product["name"], refurb_matches, new_matches, retailer_results
                ) or sent

            if sent:
                conn.execute(
                    "UPDATE alerts SET notified_at = ?, active = 0 WHERE id = ?",
                    (now, alert["id"]),
                )

        conn.commit()


def background_monitor():
    """Background thread: premium every 15s, standard every 90s, free every 15 min."""
    time.sleep(10)

    free_interval = CHECK_INTERVAL_FREE * 60
    pro_interval = CHECK_INTERVAL_PRO
    ultra_interval = CHECK_INTERVAL_ULTRA
    refurb_scrape_interval = 120
    new_scrape_interval = 300

    time_since_free = free_interval
    time_since_pro = pro_interval
    time_since_refurb_scrape = refurb_scrape_interval
    time_since_new_scrape = new_scrape_interval

    while True:
        try:
            time_since_refurb_scrape += ultra_interval
            if time_since_refurb_scrape >= refurb_scrape_interval:
                update_refurbished_cache()
                time_since_refurb_scrape = 0

            time_since_new_scrape += ultra_interval
            if time_since_new_scrape >= new_scrape_interval:
                update_new_products_cache()
                time_since_new_scrape = 0

            with get_db_connection() as conn:
                refurb_rows = conn.execute(
                    "SELECT * FROM refurbished_products WHERE available = 1"
                ).fetchall()
                refurbished = [dict(r) for r in refurb_rows]

                new_rows = conn.execute(
                    "SELECT * FROM new_products WHERE buyable = 1"
                ).fetchall()
                new_products = [dict(r) for r in new_rows]

            process_alerts("ultra", refurbished, new_products)

            time_since_pro += ultra_interval
            if time_since_pro >= pro_interval:
                process_alerts("pro", refurbished, new_products)
                time_since_pro = 0

            time_since_free += ultra_interval
            if time_since_free >= free_interval:
                process_alerts("free", refurbished, new_products)
                time_since_free = 0

        except Exception as exc:
            logger.error("Monitor error: %s", exc)

        time.sleep(ultra_interval)


# ============================================================================
# API Routes
# ============================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/products")
def api_products():
    return jsonify({"products": PRODUCTS, "categories": CATEGORIES})


@app.route("/api/availability/<product_id>")
def api_availability(product_id):
    """Check if a product is currently available across all sources."""
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    memory = request.args.get("memory", "").strip()

    db = get_db()

    # Check refurbished
    refurbished = db.execute(
        "SELECT * FROM refurbished_products WHERE category = ? AND available = 1",
        (product["category"],),
    ).fetchall()
    refurb_matches = match_product_to_refurbished(product, [dict(r) for r in refurbished])
    if memory:
        refurb_matches = [m for m in refurb_matches if memory.lower() + "gb" in m["title"].lower() or memory + " gb" in m["title"].lower()]

    # Check new
    new_rows = db.execute(
        "SELECT * FROM new_products WHERE category = ? AND buyable = 1",
        (product["category"],),
    ).fetchall()
    new_matches = match_product_to_new(product, [dict(r) for r in new_rows])

    seen_urls = set()
    unique_new = []
    for m in new_matches:
        if m["url"] not in seen_urls:
            seen_urls.add(m["url"])
            unique_new.append(m)

    # Search third-party retailers (parallel, cached)
    retailer_results = search_all_retailers(product, memory=memory or None)

    response = {
        "product_id": product_id,
        "new": {
            "available": len(unique_new) > 0,
            "count": len(unique_new),
            "listings": [dict(m) for m in unique_new[:10]],
        },
        "refurbished": {
            "available": len(refurb_matches) > 0,
            "count": len(refurb_matches),
            "listings": [dict(m) for m in refurb_matches[:20]],
        },
    }

    for retailer_name, data in retailer_results.items():
        listings = data.get("listings", [])
        response[retailer_name] = {
            "available": len(listings) > 0,
            "count": len(listings),
            "listings": listings[:10],
            "search_url": data.get("search_url", ""),
        }

    return jsonify(response)


@app.route("/api/inventory/summary")
def api_inventory_summary():
    """Summary of currently available products (new and refurbished)."""
    db = get_db()

    refurb_rows = db.execute("""
        SELECT category, COUNT(*) as count
        FROM refurbished_products
        WHERE available = 1
        GROUP BY category
    """).fetchall()
    refurb_summary = {r["category"]: r["count"] for r in refurb_rows}
    refurb_total = sum(refurb_summary.values())

    new_total = db.execute(
        "SELECT COUNT(DISTINCT url) as cnt FROM new_products WHERE buyable = 1"
    ).fetchone()["cnt"]

    # Retailer cache counts
    bestbuy_count = 0
    bh_count = 0
    swappa_count = 0
    try:
        retailer_rows = db.execute(
            "SELECT retailer, data FROM retailer_cache"
        ).fetchall()
        for row in retailer_rows:
            try:
                data = json.loads(row["data"])
                count = len(data.get("listings", []))
                if row["retailer"] == "bestbuy":
                    bestbuy_count += count
                elif row["retailer"] == "bh":
                    bh_count += count
                elif row["retailer"] == "swappa":
                    swappa_count += count
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception:
        pass

    return jsonify({
        "new_total": new_total,
        "refurbished_total": refurb_total,
        "refurbished_categories": refurb_summary,
        "bestbuy_total": bestbuy_count,
        "bh_total": bh_count,
        "swappa_total": swappa_count,
        "combined_total": new_total + refurb_total,
    })


@app.route("/api/alerts", methods=["POST"])
def api_create_alert():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    product_id = data.get("product_id", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    notify_email = bool(data.get("notify_email", False))
    notify_sms = bool(data.get("notify_sms", False))
    tier = data.get("tier", "free").strip().lower()

    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    if tier not in ("free", "pro", "ultra"):
        return jsonify({"error": "Invalid tier."}), 400
    if tier == "free" and notify_sms:
        return jsonify({"error": "SMS notifications require a paid plan (Pro or Ultra)."}), 400
    if not notify_email and not notify_sms:
        return jsonify({"error": "Select at least one notification method"}), 400
    if notify_email and not email:
        return jsonify({"error": "Email address required"}), 400
    if notify_sms and not phone:
        return jsonify({"error": "Phone number required"}), 400
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email address"}), 400

    user_id = data.get("user_id", "")
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()

    # Check if product is currently available (new or refurbished)
    refurbished = db.execute(
        "SELECT * FROM refurbished_products WHERE category = ? AND available = 1",
        (product["category"],),
    ).fetchall()
    refurb_matches = match_product_to_refurbished(product, [dict(r) for r in refurbished])

    new_rows = db.execute(
        "SELECT * FROM new_products WHERE category = ? AND buyable = 1",
        (product["category"],),
    ).fetchall()
    new_matches = match_product_to_new(product, [dict(r) for r in new_rows])

    retailer_results = search_all_retailers(product)
    has_retailer_hits = any(rdata.get("listings") for rdata in retailer_results.values())

    if refurb_matches or new_matches or has_retailer_hits:
        db.execute("""
            INSERT INTO alerts (product_id, email, phone, notify_email, notify_sms, tier, user_id, created_at, notified_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (product_id, email, phone, int(notify_email), int(notify_sms), tier, user_id, now, now))
        db.commit()

        def _notify():
            if notify_email and email:
                send_email_notification(email, product["name"], refurb_matches, new_matches, retailer_results)
            if notify_sms and phone:
                send_sms_notification(phone, product["name"], refurb_matches, new_matches, retailer_results)

        threading.Thread(target=_notify, daemon=True).start()

        msg_parts = []
        if new_matches:
            msg_parts.append("available new on Apple.com")
        if refurb_matches:
            msg_parts.append(f"{len(refurb_matches)} refurbished listing(s)")
        for rname, rdata in retailer_results.items():
            if rdata.get("listings"):
                label = {"bestbuy": "Best Buy", "bh": "B&H Photo", "swappa": "Swappa"}.get(rname, rname)
                msg_parts.append(f"{len(rdata['listings'])} at {label}")

        return jsonify({
            "status": "available_now",
            "message": f"{product['name']} is {', '.join(msg_parts)}! Sending notification...",
            "new_count": len(new_matches),
            "refurb_count": len(refurb_matches),
        })
    else:
        db.execute("""
            INSERT INTO alerts (product_id, email, phone, notify_email, notify_sms, tier, user_id, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (product_id, email, phone, int(notify_email), int(notify_sms), tier, user_id, now))
        db.commit()

        return jsonify({
            "status": "watching",
            "message": f"Alert set! We'll notify you when {product['name']} becomes available on the Apple Store.",
        })


@app.route("/api/alerts/check", methods=["GET"])
def api_check_alerts():
    db = get_db()
    active = db.execute("SELECT COUNT(*) as cnt FROM alerts WHERE active = 1").fetchone()["cnt"]
    total = db.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()["cnt"]
    return jsonify({"active_alerts": active, "total_alerts": total})


# ============================================================================
# Authentication
# ============================================================================

def verify_firebase_token(id_token):
    if not FIREBASE_AVAILABLE:
        return None
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception:
        return None


def get_or_create_user(firebase_uid, email, display_name, provider):
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET last_login = ?, email = ? WHERE firebase_uid = ?",
                (now, email, firebase_uid),
            )
            conn.commit()
            return dict(row)
        conn.execute("""
            INSERT INTO users (firebase_uid, email, display_name, provider, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firebase_uid, email, display_name, provider, now, now))
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,)
        ).fetchone()
        return dict(row)


@app.route("/api/config")
def api_config():
    firebase_config = {}
    api_key = os.getenv("FIREBASE_API_KEY", "")
    if api_key:
        firebase_config = {
            "apiKey": api_key,
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        }
    return jsonify({
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
        "firebase": firebase_config,
        "has_stripe": bool(stripe.api_key and STRIPE_PRICE_PRO and STRIPE_PRICE_ULTRA),
        "has_firebase": bool(api_key),
    })


@app.route("/api/auth/session", methods=["POST"])
def api_auth_session():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    id_token = data.get("id_token", "")
    if not id_token:
        return jsonify({"error": "Missing ID token"}), 400

    claims = verify_firebase_token(id_token)
    if not claims:
        return jsonify({"error": "Invalid or expired token"}), 401

    uid = claims.get("uid", "")
    email = claims.get("email", "")
    name = claims.get("name", "")
    provider = claims.get("firebase", {}).get("sign_in_provider", "unknown")

    user = get_or_create_user(uid, email, name, provider)
    return jsonify({
        "user_id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "phone": user.get("phone", ""),
        "has_stripe": bool(user.get("stripe_customer_id")),
    })


# ============================================================================
# Stripe Subscriptions
# ============================================================================

@app.route("/api/create-subscription", methods=["POST"])
def api_create_subscription():
    if not stripe.api_key:
        return jsonify({"error": "Payment processing is not configured."}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    payment_method_id = data.get("payment_method_id", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    product_id = data.get("product_id", "").strip()
    tier = data.get("tier", "").strip().lower()
    notify_email = bool(data.get("notify_email", True))
    notify_sms = bool(data.get("notify_sms", False))
    user_id = data.get("user_id", "")

    if tier not in ("pro", "ultra"):
        return jsonify({"error": "Invalid tier for subscription."}), 400
    if not payment_method_id:
        return jsonify({"error": "Payment method required."}), 400
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Valid email address required."}), 400
    if notify_sms and not phone:
        return jsonify({"error": "Phone number required for SMS alerts."}), 400

    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Invalid product."}), 400

    price_id = STRIPE_PRICE_PRO if tier == "pro" else STRIPE_PRICE_ULTRA
    if not price_id:
        return jsonify({"error": "Subscription pricing not configured."}), 503

    try:
        customer = stripe.Customer.create(
            email=email,
            payment_method=payment_method_id,
            invoice_settings={"default_payment_method": payment_method_id},
            metadata={"phone": phone, "product_id": product_id, "tier": tier},
        )

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )

        if subscription.status == "active":
            _create_paid_alert(product_id, email, phone, notify_email, notify_sms,
                               tier, customer.id, subscription.id, user_id)
            return jsonify({
                "status": "active",
                "message": f"Subscribed to {tier.title()} plan! Alert set for {product['name']}.",
                "subscription_id": subscription.id,
            })

        pi = subscription.latest_invoice.payment_intent
        if pi and pi.status == "requires_action":
            return jsonify({
                "status": "requires_action",
                "client_secret": pi.client_secret,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
            })

        if pi and pi.status == "succeeded":
            _create_paid_alert(product_id, email, phone, notify_email, notify_sms,
                               tier, customer.id, subscription.id, user_id)
            return jsonify({
                "status": "active",
                "message": f"Subscribed to {tier.title()} plan! Alert set for {product['name']}.",
                "subscription_id": subscription.id,
            })

        return jsonify({"error": f"Unexpected status: {subscription.status}"}), 400

    except Exception as e:
        if hasattr(e, "user_message"):
            return jsonify({"error": e.user_message}), 400
        logger.error("Subscription creation failed: %s", e)
        return jsonify({"error": "Payment processing failed. Please try again."}), 500


@app.route("/api/confirm-subscription", methods=["POST"])
def api_confirm_subscription():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    subscription_id = data.get("subscription_id", "")
    customer_id = data.get("customer_id", "")
    product_id = data.get("product_id", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    tier = data.get("tier", "").strip()
    notify_email = bool(data.get("notify_email", True))
    notify_sms = bool(data.get("notify_sms", False))
    user_id = data.get("user_id", "")

    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        if sub.status == "active":
            _create_paid_alert(product_id, email, phone, notify_email, notify_sms,
                               tier, customer_id, subscription_id, user_id)
            product = get_product_by_id(product_id)
            name = product["name"] if product else "your product"
            return jsonify({
                "status": "active",
                "message": f"Subscribed to {tier.title()} plan! Alert set for {name}.",
            })
        return jsonify({"error": "Payment was not completed."}), 400
    except Exception as e:
        logger.error("Subscription confirmation failed: %s", e)
        return jsonify({"error": "Could not confirm subscription."}), 500


def _create_paid_alert(product_id, email, phone, notify_email, notify_sms,
                       tier, customer_id, subscription_id, user_id=None):
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO alerts (product_id, email, phone, notify_email, notify_sms, tier,
                              stripe_customer_id, stripe_subscription_id, user_id, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (product_id, email, phone, int(notify_email), int(notify_sms), tier,
              customer_id, subscription_id, user_id, now))
        conn.commit()


# ============================================================================
# Startup
# ============================================================================

init_db()

monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
