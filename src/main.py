"""Asynchronous catalog harvester for Lucy & Yak Shopify store."""

import argparse
import asyncio
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from config.settings import (
    BASE_URL,
    HEADERS,
    INITIAL_BACKOFF,
    MAX_RETRIES,
    PAGE_LIMIT,
    PROCESSED_DATA_PATH,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
)
from src.logger import logger
from src.pipeline import clean_product_data, load_existing_product_ids, save_jsonl_batch


async def fetch_catalog_page(
    client: httpx.AsyncClient,
    page: int,
    limit: int = PAGE_LIMIT,
) -> Optional[List[Dict[str, Any]]]:
    """Fetches a single page of products from the public Shopify catalog endpoint.

    Args:
        client: Active HTTPX AsyncClient session.
        page: Page number (1-indexed).
        limit: Max products per page (up to 250).

    Returns:
        List of raw product dictionaries, or None if fatal error occurred.
    """
    url = f"{BASE_URL}/products.json?limit={limit}&page={page}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Human-like polite jitter between requests
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            await asyncio.sleep(delay)

            response = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                try:
                    payload = response.json()
                    return payload.get("products", [])
                except Exception as json_err:
                    logger.warning(f"Failed to parse JSON for {url}: {json_err}")
                    return None

            if response.status_code == 429:
                backoff = INITIAL_BACKOFF * attempt + random.uniform(0.5, 2.0)
                logger.warning(
                    f"Rate limit encountered (429) on page {page}. "
                    f"Backing off for {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})..."
                )
                await asyncio.sleep(backoff)
                continue

            if response.status_code == 404:
                logger.warning(f"Catalog page not found (404): {url}")
                return []

            logger.warning(
                f"Unexpected status {response.status_code} for page {page} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )
            await asyncio.sleep(2.0 * attempt)

        except (httpx.RequestError, httpx.TimeoutException) as exc:
            logger.error(f"Network error requesting page {page} (attempt {attempt}): {exc}")
            await asyncio.sleep(2.0 * attempt)

    logger.error(f"Exhausted all {MAX_RETRIES} attempts for page {page}.")
    return None


async def harvest_catalog(
    output_path: Path = PROCESSED_DATA_PATH,
    start_page: int = 1,
    max_pages: Optional[int] = None,
    overwrite: bool = False,
    page_limit: int = PAGE_LIMIT,
) -> None:
    """Orchestrates asynchronous bulk harvesting of the entire Shopify product catalog.

    Args:
        output_path: File path to save cleaned JSONL data.
        start_page: Page number to start harvesting from.
        max_pages: Optional cap on maximum number of pages to fetch.
        overwrite: If True, overwrite the target file; if False, resume and deduplicate.
        page_limit: Max items per page request.
    """
    logger.info("=== Starting Lucy & Yak Shopify Harvester ===")
    start_time = time.time()

    # Manage existing dataset and deduplication
    existing_ids: Set[int] = set()
    write_mode = "w" if overwrite else "a"

    if overwrite and output_path.exists():
        logger.info(f"Overwrite flag is active. Existing file at {output_path} will be overwritten.")
    elif not overwrite:
        existing_ids = load_existing_product_ids(output_path)
        logger.info(f"Loaded {len(existing_ids)} existing product IDs to prevent duplicates.")

    total_pages_fetched = 0
    total_products_fetched = 0
    new_products_saved = 0
    current_page = start_page

    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            if max_pages and total_pages_fetched >= max_pages:
                logger.info(f"Reached user-configured maximum pages cap ({max_pages}).")
                break

            logger.info(f"Fetching page {current_page} (limit={page_limit})...")
            products = await fetch_catalog_page(client, page=current_page, limit=page_limit)

            if products is None:
                logger.error(f"Terminating harvesting due to repeated failure on page {current_page}.")
                break

            # Dynamic stop condition: Shopify returns an empty list when all pages are exhausted
            if not products:
                logger.info(f"Page {current_page} returned 0 products. Catalog end reached.")
                break

            total_pages_fetched += 1
            total_products_fetched += len(products)

            cleaned_batch: List[Dict[str, Any]] = []
            for raw_prod in products:
                prod_id = raw_prod.get("id")
                if prod_id in existing_ids:
                    continue

                cleaned = clean_product_data(raw_prod)
                if cleaned:
                    cleaned_batch.append(cleaned)
                    if prod_id is not None:
                        existing_ids.add(int(prod_id))

            # Batch write all cleaned products from this page
            if cleaned_batch:
                written = save_jsonl_batch(cleaned_batch, file_path=output_path, mode=write_mode)
                new_products_saved += written
                # After first write, subsequent page writes must be append ('a')
                write_mode = "a"

            logger.info(
                f"Page {current_page}: fetched {len(products)}, "
                f"saved {len(cleaned_batch)} new (Total new saved: {new_products_saved})."
            )

            current_page += 1

    elapsed = time.time() - start_time
    logger.info("=== Harvesting Completed Successfully ===")
    logger.info(f"Time Elapsed: {elapsed:.2f} seconds")
    logger.info(f"Pages Fetched: {total_pages_fetched}")
    logger.info(f"Total Products Encountered: {total_products_fetched}")
    logger.info(f"New Products Saved: {new_products_saved}")
    logger.info(f"Output Destination: {output_path}")


def main() -> None:
    """CLI parser and runner."""
    parser = argparse.ArgumentParser(
        description="High-performance Shopify catalog harvester for Lucy & Yak."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_PATH,
        help="Destination path for cleaned JSONL output.",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Page to begin scraping from (default: 1).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional maximum number of pages to fetch.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=PAGE_LIMIT,
        help="Number of products per page request (default: 250).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output file instead of appending/deduplicating.",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            harvest_catalog(
                output_path=args.output,
                start_page=args.start_page,
                max_pages=args.max_pages,
                overwrite=args.overwrite,
                page_limit=args.limit,
            )
        )
    except KeyboardInterrupt:
        logger.warning("\nHarvesting interrupted by user. Saved records remain intact.")
        sys.exit(0)


if __name__ == "__main__":
    main()
