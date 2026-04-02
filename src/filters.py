"""Product alert filters.

Allows users to define criteria so they only receive alerts for products
they care about, rather than every single refurbished listing.
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

DEFAULT_FILTERS_PATH = os.path.join(os.path.dirname(__file__), "..", "filters.json")

# Example filters.json structure:
# {
#   "alerts": [
#     {
#       "name": "Cheap MacBook Air",
#       "category": "mac",
#       "keywords": ["macbook air"],
#       "max_price": 1000
#     },
#     {
#       "name": "Any iPad Pro",
#       "category": "ipad",
#       "keywords": ["ipad pro"],
#       "max_price": null
#     },
#     {
#       "name": "Apple Watch Ultra",
#       "keywords": ["watch ultra"],
#       "max_price": 700
#     }
#   ]
# }


def load_filters(path: str = DEFAULT_FILTERS_PATH) -> list[dict]:
    """Load alert filters from the filters.json file.

    Returns:
        List of filter dicts, or empty list if no filters are configured
        (which means all products will trigger alerts).
    """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logger.info("No filters.json found — all products will trigger alerts.")
        return []

    try:
        with open(path, "r") as f:
            data = json.load(f)
        filters = data.get("alerts", [])
        logger.info("Loaded %d alert filter(s) from %s", len(filters), path)
        return filters
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load filters: %s", exc)
        return []


def matches_filter(product: dict, alert_filter: dict) -> bool:
    """Check if a product matches a single alert filter.

    Args:
        product: Normalized product dict.
        alert_filter: Filter dict with optional keys: category, keywords, max_price, min_price.

    Returns:
        True if the product matches all specified criteria.
    """
    # Check category
    if "category" in alert_filter and alert_filter["category"]:
        if product.get("category", "").lower() != alert_filter["category"].lower():
            return False

    # Check keywords (all keywords must appear in the title)
    if "keywords" in alert_filter and alert_filter["keywords"]:
        title_lower = product.get("title", "").lower()
        for keyword in alert_filter["keywords"]:
            if not re.search(re.escape(keyword.lower()), title_lower):
                return False

    # Check max price
    if "max_price" in alert_filter and alert_filter["max_price"] is not None:
        try:
            price = float(product.get("price", "0").replace(",", ""))
            if price > float(alert_filter["max_price"]):
                return False
        except (ValueError, TypeError):
            pass

    # Check min price
    if "min_price" in alert_filter and alert_filter["min_price"] is not None:
        try:
            price = float(product.get("price", "0").replace(",", ""))
            if price < float(alert_filter["min_price"]):
                return False
        except (ValueError, TypeError):
            pass

    return True


def apply_filters(products: list[dict], filters: list[dict]) -> list[dict]:
    """Filter a list of products against the configured alert filters.

    If no filters are configured, all products are returned (no filtering).

    Args:
        products: List of normalized product dicts.
        filters: List of alert filter dicts.

    Returns:
        List of products matching at least one filter.
    """
    if not filters:
        return products

    matched = []
    for product in products:
        for f in filters:
            if matches_filter(product, f):
                matched.append(product)
                break  # Don't add duplicates

    logger.info("Filters matched %d of %d products", len(matched), len(products))
    return matched
