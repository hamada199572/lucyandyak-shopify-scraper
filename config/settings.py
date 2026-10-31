"""Configuration settings for Lucy & Yak Shopify Harvester."""

from pathlib import Path

# Base Paths (anchored to project root)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

RAW_DATA_PATH = RAW_DATA_DIR / "products_raw.jsonl"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "products_cleaned.jsonl"
LOG_FILE_PATH = LOGS_DIR / "scraper.log"

# Target Store
BASE_URL = "https://lucyandyak.com"

# Realistic Browser Emulation Headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://lucyandyak.com/",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
}

# Request and Rate Limiting Settings
PAGE_LIMIT = 250
REQUEST_TIMEOUT = 25.0
REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 2.0
MAX_RETRIES = 5
INITIAL_BACKOFF = 5.0
