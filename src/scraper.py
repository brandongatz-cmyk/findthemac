"""Scraper for Apple's refurbished product pages.

Fetches product data from Apple's refurbished store by extracting the
REFURB_GRID_BOOTSTRAP JavaScript object embedded in each category page.
"""

import json
import logging
import re
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.apple.com/shop/refurbished"

CATEGORIES = [
    "mac",
    "ipad",
    "iphone",
    "watch",
    "airpods",
    "appletv",
    "homepod",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Regex to extract the REFURB_GRID_BOOTSTRAP JSON object from the page HTML.
BOOTSTRAP_PATTERN = re.compile(
    r"window\.REFURB_GRID_BOOTSTRAP\s*=\s*(\{.*?\});\s*$",
    re.MULTILINE | re.DOTALL,
)


def fetch_category(category: str, retries: int = 3) -> list[dict]:
    """Fetch all refurbished products for a given category.

    Args:
        category: Product category slug (e.g. "mac", "ipad").
        retries: Number of retry attempts on failure.

    Returns:
        List of product tile dicts extracted from the page.
    """
    url = f"{BASE_URL}/{category}"
    last_error = None

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            match = BOOTSTRAP_PATTERN.search(response.text)
            if not match:
                logger.warning("No REFURB_GRID_BOOTSTRAP found on %s", url)
                return []

            data = json.loads(match.group(1))
            tiles = data.get("tiles", [])
            logger.info("Found %d products in category '%s'", len(tiles), category)
            return tiles

        except (requests.RequestException, json.JSONDecodeError) as exc:
            last_error = exc
            wait = 2 ** attempt
            logger.warning(
                "Attempt %d/%d failed for %s: %s — retrying in %ds",
                attempt + 1, retries, url, exc, wait,
            )
            time.sleep(wait)

    logger.error("Failed to fetch %s after %d attempts: %s", url, retries, last_error)
    return []


def normalize_product(tile: dict, category: str) -> dict:
    """Convert a raw tile dict into a normalized product record.

    Args:
        tile: Raw product tile from REFURB_GRID_BOOTSTRAP.
        category: The category this product was found in.

    Returns:
        Normalized product dict with consistent keys.
    """
    price_info = tile.get("price", {})
    current = price_info.get("currentPrice", {})
    return {
        "part_number": tile.get("partNumber", ""),
        "title": tile.get("title", ""),
        "url": "https://www.apple.com" + tile.get("productDetailsUrl", ""),
        "category": category,
        "price": current.get("raw_amount", ""),
        "original_price": price_info.get("originalProductAmount", ""),
        "savings": price_info.get("savings", ""),
        "currency": price_info.get("priceCurrency", "USD"),
        "shipping": tile.get("omnitureModel", {}).get("customerCommitString", ""),
    }


def fetch_all_products(categories: list[str] | None = None) -> list[dict]:
    """Fetch and normalize products across all specified categories.

    Args:
        categories: List of category slugs to scrape. Defaults to all.

    Returns:
        List of normalized product dicts.
    """
    if categories is None:
        categories = CATEGORIES

    all_products = []
    for category in categories:
        tiles = fetch_category(category)
        for tile in tiles:
            product = normalize_product(tile, category)
            if product["part_number"]:
                all_products.append(product)
        # Be polite to Apple's servers
        time.sleep(1)

    logger.info("Total products fetched: %d", len(all_products))
    return all_products
