"""Product availability tracker.

Maintains a local JSON database of previously seen products and detects
when new products appear (i.e. were previously unavailable or not listed).
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")


class ProductTracker:
    """Tracks Apple refurbished product availability over time."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self.products: dict[str, dict] = {}
        self._load()

    def _load(self):
        """Load existing product database from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    self.products = json.load(f)
                logger.info("Loaded %d tracked products from %s", len(self.products), self.db_path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Failed to load product database: %s", exc)
                self.products = {}
        else:
            logger.info("No existing database found. Starting fresh.")

    def _save(self):
        """Persist the product database to disk."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w") as f:
            json.dump(self.products, f, indent=2)
        logger.debug("Saved %d products to %s", len(self.products), self.db_path)

    def update(self, current_products: list[dict]) -> dict:
        """Update the tracker with the latest product list.

        Compares the incoming product list against the stored database to
        identify newly available products, returned products, and products
        that are no longer listed.

        Args:
            current_products: List of normalized product dicts from the scraper.

        Returns:
            Dict with keys:
                - "new": Products never seen before (brand new listings).
                - "back_in_stock": Products previously seen, then gone, now back.
                - "removed": Products that were available last check but are now gone.
        """
        now = datetime.now(timezone.utc).isoformat()
        current_ids = set()
        new_products = []
        back_in_stock = []

        for product in current_products:
            part_num = product["part_number"]
            current_ids.add(part_num)

            if part_num not in self.products:
                # Never seen before — brand new listing
                self.products[part_num] = {
                    **product,
                    "first_seen": now,
                    "last_seen": now,
                    "available": True,
                    "last_status_change": now,
                }
                new_products.append(product)
            else:
                existing = self.products[part_num]
                existing["last_seen"] = now
                # Update price in case it changed
                existing["price"] = product["price"]
                existing["savings"] = product["savings"]

                if not existing.get("available", False):
                    # Was previously unavailable — it's back!
                    existing["available"] = True
                    existing["last_status_change"] = now
                    back_in_stock.append(product)

        # Identify removed products (were available, now not in current listing)
        removed = []
        for part_num, stored in self.products.items():
            if part_num not in current_ids and stored.get("available", False):
                stored["available"] = False
                stored["last_status_change"] = now
                removed.append(stored)

        self._save()

        logger.info(
            "Tracker update: %d new, %d back in stock, %d removed",
            len(new_products), len(back_in_stock), len(removed),
        )

        return {
            "new": new_products,
            "back_in_stock": back_in_stock,
            "removed": removed,
        }

    @property
    def is_first_run(self) -> bool:
        """Returns True if the tracker has no prior data (first run)."""
        return len(self.products) == 0
