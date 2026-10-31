# Lucy & Yak Shopify Harvester

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, asynchronous data harvesting and ETL pipeline designed to extract, clean, and store the entire product catalog from the **Lucy & Yak** Shopify storefront (`lucyandyak.com`).

---

## 🚀 Key Features

* **Direct Catalog API Extraction:** Queries Shopify's native storefront endpoint (`/products.json?limit=250`) rather than parsing fragile HTML DOM structures.
* **Fully Asynchronous Architecture:** Built on top of `httpx.AsyncClient` and Python's `asyncio` for non-blocking network I/O.
* **Idempotent & Deduplicated:** Automatically loads existing product IDs before harvesting to prevent duplicate records on recurring runs.
* **Batch I/O Optimization:** Writes data to disk in per-page chunks rather than repeated individual file opens, maximizing disk efficiency.
* **Smart Rate-Limit Resilience:** Dynamically handles HTTP 429 status codes with exponential backoff and randomized jitter.
* **Robust Path Resolution:** All paths are anchored to the project root using `pathlib.Path`, allowing execution from any working directory or cron scheduler.
* **Rotating Log System:** Implements thread-safe rotating file logs alongside formatted console outputs.
* **Flexible CLI Interface:** Easily customize page limits, start pages, max pages, and output file destinations via command-line arguments.

---

## 📁 Project Structure

```text
lucyandyak-shopify-scraper/
│
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized settings, endpoints, headers, and paths
│
├── src/
│   ├── __init__.py
│   ├── logger.py            # Rotating file and console logger
│   ├── pipeline.py          # Data cleaning, deduplication, and JSONL persistence
│   ├── scraper.py           # Single-product query utility (by handle)
│   └── main.py              # Asynchronous bulk catalog harvester CLI
│
├── data/
│   ├── raw/                 # Raw payloads (if stored)
│   └── processed/           # Standardized JSONL output files
│
├── logs/                    # Rotating log files
│   └── scraper.log
│
├── .gitignore               # Comprehensive Git ignore rules
├── requirements.txt         # Minimal, pinned dependencies
└── README.md                # Documentation and usage guide
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hamada199572/lucyandyak-shopify-scraper.git
cd lucyandyak-shopify-scraper
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚡ Usage

### Full Catalog Harvesting

To run the asynchronous harvester and fetch all products into `data/processed/products_cleaned.jsonl`:

```bash
python -m src.main
```

### Advanced CLI Options

```bash
# Fetch up to 2 pages starting from page 1
python -m src.main --start-page 1 --max-pages 2

# Overwrite existing records instead of deduplicating/appending
python -m src.main --overwrite

# Save to a custom output file
python -m src.main --output data/processed/my_custom_export.jsonl

# Inspect all available options
python -m src.main --help
```

### Fetch a Single Product by Handle

To inspect or debug a single product by its URL slug/handle:

```bash
python -m src.scraper --handle yolanda-bed-set-in-red-gingham
```

---

## 📊 Output Data Schema (JSONL)

Each record in `products_cleaned.jsonl` is a valid JSON line with the following structure:

```json
{
  "id": 7148786319463,
  "title": "Etta - Cotton Jersey Sleeveless Tank in Black",
  "handle": "etta-sleeveless-cotton-tee-in-black",
  "product_type": "Tops",
  "vendor": "Lucy & Yak",
  "tags": ["Tops", "Cotton", "Summer"],
  "created_at": "2024-10-31T14:58:28+00:00",
  "updated_at": "2024-10-31T15:00:00+00:00",
  "published_at": "2024-10-31T15:00:00+00:00",
  "variants": [
    {
      "id": 58320089809270,
      "title": "Black Cord / XXS (UK 4)",
      "price": "26.00",
      "compare_at_price": null,
      "sku": "ETA-BLA-COT-001-XXS",
      "available": false
    }
  ],
  "images": [
    "https://cdn.shopify.com/s/files/1/1979/9235/files/ETTA_SLEEVLESS_TANK_BLACK4.jpg"
  ]
}
```

---

## 🛡️ Best Practices & Quality Standards

* **No Blind Scraping:** Uses Shopify's native JSON feed with configurable headers mimicking standard desktop browser clients.
* **Polite Interval Delays:** Human-like randomized jitter delays between 1.0s and 2.0s between requests prevent accidental service disruptions.
* **Strict Type Hints & PEP 8:** Entire codebase is typed and documented with clean Google-style docstrings.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
