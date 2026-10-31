"""Unit tests for the catalog harvester."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from src.main import fetch_catalog_page, harvest_catalog
from src.pipeline import load_existing_product_ids


class TestMainHarvester(unittest.TestCase):

    @patch("httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_fetch_catalog_page_success(self, mock_get):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {"id": 1, "title": "P1", "handle": "p1"},
                {"id": 2, "title": "P2", "handle": "p2"},
            ]
        }
        mock_get.return_value = mock_response

        client = MagicMock(spec=httpx.AsyncClient)
        client.get = mock_get

        import asyncio
        products = asyncio.run(fetch_catalog_page(client, page=1, limit=250))
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["id"], 1)

    @patch("src.main.fetch_catalog_page", new_callable=AsyncMock)
    def test_harvest_catalog_deduplication(self, mock_fetch):
        # Page 1 returns products 1 and 2
        # Page 2 returns product 3
        # Page 3 returns empty list (catalog finished)
        mock_fetch.side_effect = [
            [
                {"id": 1, "title": "Product 1", "handle": "p1"},
                {"id": 2, "title": "Product 2", "handle": "p2"},
            ],
            [
                {"id": 3, "title": "Product 3", "handle": "p3"},
            ],
            [],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "harvested.jsonl"

            # Pre-populate with product 1 to test deduplication
            with open(out_file, "w", encoding="utf-8") as f:
                f.write('{"id": 1, "title": "Existing Product 1"}\n')

            import asyncio
            # Run harvest
            asyncio.run(harvest_catalog(output_path=out_file, start_page=1))

            # Only products 2 and 3 should have been appended!
            final_ids = load_existing_product_ids(out_file)
            self.assertEqual(final_ids, {1, 2, 3})

            with open(out_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            # 1 initial + 2 new = exactly 3 lines (no duplicate product 1)
            self.assertEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
