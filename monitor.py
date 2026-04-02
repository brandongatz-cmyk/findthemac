#!/usr/bin/env python3
"""Apple Refurbished Product Monitor.

Periodically checks the Apple refurbished store for newly available products
and sends email and SMS alerts when items matching your filters appear.

Usage:
    # Run once (good for cron jobs):
    python monitor.py --once

    # Run continuously with built-in scheduler:
    python monitor.py

    # Run once, specific categories only:
    python monitor.py --once --categories mac,ipad

    # Dry run (no notifications sent):
    python monitor.py --once --dry-run
"""

import argparse
import logging
import os
import sys

import schedule
from dotenv import load_dotenv

from src.filters import apply_filters, load_filters
from src.notifier import (
    build_alert_email,
    build_sms_body,
    send_email,
    send_sms,
)
from src.scraper import fetch_all_products
from src.tracker import ProductTracker

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("monitor")


def get_config() -> dict:
    """Load configuration from environment variables."""
    return {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "email_from": os.getenv("EMAIL_FROM", ""),
        "email_to": os.getenv("EMAIL_TO", ""),
        "twilio_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_from": os.getenv("TWILIO_FROM_NUMBER", ""),
        "sms_to": os.getenv("SMS_TO_NUMBER", ""),
        "check_interval": int(os.getenv("CHECK_INTERVAL_MINUTES", "15")),
        "categories": os.getenv("CATEGORIES", "mac,ipad,iphone,watch,airpods,appletv,homepod").split(","),
    }


def check_products(config: dict, tracker: ProductTracker, dry_run: bool = False, categories: list[str] | None = None):
    """Run a single check cycle: scrape, detect changes, and notify."""
    cats = categories or config["categories"]
    logger.info("Checking categories: %s", ", ".join(cats))

    first_run = tracker.is_first_run
    products = fetch_all_products(cats)

    if not products:
        logger.warning("No products fetched — site may be down or categories empty.")
        return

    changes = tracker.update(products)
    new_products = changes["new"]
    back_in_stock = changes["back_in_stock"]

    if first_run:
        logger.info(
            "First run complete — indexed %d products. "
            "Alerts will fire on subsequent runs when new products appear.",
            len(products),
        )
        return

    # Apply user filters
    filters = load_filters()
    filtered_new = apply_filters(new_products, filters)
    filtered_back = apply_filters(back_in_stock, filters)

    total_alerts = len(filtered_new) + len(filtered_back)
    if total_alerts == 0:
        logger.info("No new matching products found this cycle.")
        return

    logger.info(
        "Alert! %d new listing(s), %d back-in-stock item(s) match your filters.",
        len(filtered_new), len(filtered_back),
    )

    if dry_run:
        logger.info("DRY RUN — skipping notifications.")
        for p in filtered_new + filtered_back:
            logger.info("  -> %s — $%s — %s", p["title"], p["price"], p["url"])
        return

    # Send email
    if config["smtp_username"] and config["email_to"]:
        subject, html_body, text_body = build_alert_email(filtered_new, filtered_back)
        send_email(
            smtp_host=config["smtp_host"],
            smtp_port=config["smtp_port"],
            smtp_username=config["smtp_username"],
            smtp_password=config["smtp_password"],
            from_addr=config["email_from"],
            to_addr=config["email_to"],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
    else:
        logger.warning("Email not configured — skipping email notification.")

    # Send SMS
    if config["twilio_sid"] and config["sms_to"]:
        sms_body = build_sms_body(filtered_new, filtered_back)
        send_sms(
            account_sid=config["twilio_sid"],
            auth_token=config["twilio_token"],
            from_number=config["twilio_from"],
            to_number=config["sms_to"],
            body=sms_body,
        )
    else:
        logger.warning("Twilio SMS not configured — skipping SMS notification.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Apple's refurbished store for product availability."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check and exit (useful for cron).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for products but don't send notifications.",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of categories to monitor (e.g. mac,ipad).",
    )
    args = parser.parse_args()

    config = get_config()
    tracker = ProductTracker()
    categories = args.categories.split(",") if args.categories else None

    if args.once:
        check_products(config, tracker, dry_run=args.dry_run, categories=categories)
        return

    # Continuous mode with scheduler
    interval = config["check_interval"]
    logger.info("Starting continuous monitoring every %d minute(s).", interval)

    # Run immediately on startup
    check_products(config, tracker, dry_run=args.dry_run, categories=categories)

    # Then schedule recurring checks
    schedule.every(interval).minutes.do(
        check_products, config=config, tracker=tracker, dry_run=args.dry_run, categories=categories,
    )

    try:
        while True:
            schedule.run_pending()
            import time
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
