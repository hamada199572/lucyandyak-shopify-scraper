"""Single product scraper using Shopify JSON endpoint."""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import BASE_URL, HEADERS, MAX_RETRIES, REQUEST_TIMEOUT
from src.logger import logger
from src.pipeline import clean_product_data


def fetch_product_by_handle(handle: str) -> Optional[Dict[str, Any]]:
    """Fetches raw product data for a single product handle using Shopify's JSON endpoint.

    Args:
        handle: Product slug/handle (e.g. 'yolanda-bed-set-in-red-gingham').

    Returns:
        Raw product dictionary if found, or None.
    """
    url = f"{BASE_URL}/products/{handle.strip()}.json"

    with httpx.Client(follow_redirects=True, timeout=REQUEST_TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Requesting product: {url} (Attempt {attempt}/{MAX_RETRIES})")
                response = client.get(url, headers=HEADERS)

                if response.status_code == 200:
                    data = response.json()
                    product = data.get("product")
                    if product:
                        return product
                    logger.warning(f"Payload did not contain 'product' key: {url}")
                    return None

                if response.status_code == 404:
                    logger.warning(f"Product handle not found (404): {url}")
                    return None

                if response.status_code == 429:
                    backoff = attempt * 3.0
                    logger.warning(f"Rate limited (429). Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                    continue

                logger.warning(f"Unexpected status ({response.status_code}) for: {url}")

            except httpx.RequestError as exc:
                logger.error(f"Network error requesting {url}: {exc}")
                time.sleep(2.0)

    logger.error(f"Failed to fetch product handle '{handle}' after {MAX_RETRIES} attempts.")
    return None


def main() -> None:
    """CLI entry point for querying a single product."""
    parser = argparse.ArgumentParser(description="Fetch a single product from Lucy & Yak by handle.")
    parser.add_argument(
        "--handle",
        type=str,
        default="yolanda-bed-set-in-red-gingham",
        help="Product handle slug to fetch",
    )
    args = parser.parse_args()

    logger.info(f"Starting single product fetch for handle: {args.handle}")
    raw_product = fetch_product_by_handle(args.handle)

    if raw_product:
        cleaned = clean_product_data(raw_product)
        logger.info(f"Product retrieved successfully: {cleaned.get('title')}")
        logger.info(f"Variants count: {len(cleaned.get('variants', []))}")
        logger.info(f"Images count: {len(cleaned.get('images', []))}")
    else:
        logger.error(f"Could not retrieve product '{args.handle}'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
