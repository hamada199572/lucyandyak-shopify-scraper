"""Data cleaning, transformation, and storage pipeline."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import PROCESSED_DATA_PATH
from src.logger import logger


def clean_product_data(raw_product: Dict[str, Any]) -> Dict[str, Any]:
    """Parses and cleans raw product payload into a standardized schema.

    Args:
        raw_product: Raw dictionary of a product from Shopify JSON endpoint.

    Returns:
        Structured dictionary containing cleaned product attributes.
    """
    try:
        raw_tags = raw_product.get("tags", [])
        if isinstance(raw_tags, str):
            tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
        elif isinstance(raw_tags, list):
            tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
        else:
            tags = []

        variants: List[Dict[str, Any]] = []
        for variant in raw_product.get("variants", []):
            variants.append({
                "id": variant.get("id"),
                "title": variant.get("title"),
                "price": variant.get("price"),
                "compare_at_price": variant.get("compare_at_price"),
                "sku": variant.get("sku"),
                "available": bool(variant.get("available", False)),
            })

        images: List[str] = [
            img.get("src") for img in raw_product.get("images", []) if img.get("src")
        ]

        cleaned: Dict[str, Any] = {
            "id": raw_product.get("id"),
            "title": raw_product.get("title"),
            "handle": raw_product.get("handle"),
            "product_type": raw_product.get("product_type"),
            "vendor": raw_product.get("vendor"),
            "tags": tags,
            "created_at": raw_product.get("created_at"),
            "updated_at": raw_product.get("updated_at"),
            "published_at": raw_product.get("published_at"),
            "variants": variants,
            "images": images,
        }
        return cleaned
    except Exception as exc:
        logger.error(
            f"Failed to clean product data (handle: {raw_product.get('handle', 'unknown')}): {exc}",
            exc_info=True,
        )
        return {}


def load_existing_product_ids(file_path: Union[Path, str] = PROCESSED_DATA_PATH) -> Set[int]:
    """Reads an existing JSONL file and returns the set of product IDs already stored.

    Args:
        file_path: Path to the target JSONL file.

    Returns:
        Set of integer IDs present in the file.
    """
    path = Path(file_path)
    if not path.is_file():
        return set()

    existing_ids: Set[int] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    product_id = record.get("id")
                    if product_id is not None:
                        existing_ids.add(int(product_id))
                except (json.JSONDecodeError, ValueError) as err:
                    logger.warning(f"Skipping malformed line {line_number} in {path}: {err}")
    except Exception as exc:
        logger.error(f"Error reading existing IDs from {path}: {exc}")

    return existing_ids


def save_jsonl_batch(
    records: Iterable[Dict[str, Any]],
    file_path: Union[Path, str] = PROCESSED_DATA_PATH,
    mode: str = "a",
) -> int:
    """Appends or writes a batch of records to a JSONL file efficiently.

    Args:
        records: An iterable of cleaned dictionary records.
        file_path: Path to the target JSONL file.
        mode: File write mode ('a' for append, 'w' for overwrite).

    Returns:
        Number of successfully written records.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    written_count = 0
    try:
        with open(path, mode, encoding="utf-8") as f:
            for record in records:
                if not record:
                    continue
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                written_count += 1
        return written_count
    except Exception as exc:
        logger.error(f"Failed to write batch to {path}: {exc}", exc_info=True)
        return written_count


def save_jsonl(
    data: Dict[str, Any],
    file_path: Union[Path, str] = PROCESSED_DATA_PATH,
) -> bool:
    """Saves a single dictionary as a line in a JSONL file."""
    return save_jsonl_batch([data], file_path=file_path, mode="a") == 1
