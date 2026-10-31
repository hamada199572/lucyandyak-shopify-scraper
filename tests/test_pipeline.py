"""Unit tests for the data processing pipeline."""

import json
import tempfile
import unittest
from pathlib import Path
from src.pipeline import clean_product_data, load_existing_product_ids, save_jsonl_batch, save_jsonl


class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.sample_raw_product = {
            "id": 999111,
            "title": "Organic Cotton Dungarees - Original",
            "handle": "original-dungarees-black",
            "product_type": "Dungarees",
            "vendor": "Lucy & Yak",
            "tags": "Organic, Cotton, Classic",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
            "published_at": "2024-01-01T11:00:00Z",
            "variants": [
                {
                    "id": 1001,
                    "title": "Black / 30in",
                    "price": "68.00",
                    "compare_at_price": "75.00",
                    "sku": "DUN-BLA-30",
                    "available": True,
                },
                {
                    "id": 1002,
                    "title": "Black / 32in",
                    "price": "68.00",
                    "compare_at_price": None,
                    "sku": "DUN-BLA-32",
                    "available": False,
                },
            ],
            "images": [
                {"src": "https://cdn.shopify.com/files/img1.jpg"},
                {"src": "https://cdn.shopify.com/files/img2.jpg"},
            ],
        }

    def test_clean_product_data_standard(self):
        cleaned = clean_product_data(self.sample_raw_product)

        self.assertEqual(cleaned["id"], 999111)
        self.assertEqual(cleaned["title"], "Organic Cotton Dungarees - Original")
        self.assertEqual(cleaned["handle"], "original-dungarees-black")
        self.assertEqual(cleaned["product_type"], "Dungarees")
        self.assertEqual(cleaned["vendor"], "Lucy & Yak")
        self.assertEqual(cleaned["tags"], ["Organic", "Cotton", "Classic"])
        self.assertEqual(len(cleaned["variants"]), 2)
        self.assertEqual(cleaned["variants"][0]["sku"], "DUN-BLA-30")
        self.assertTrue(cleaned["variants"][0]["available"])
        self.assertFalse(cleaned["variants"][1]["available"])
        self.assertEqual(
            cleaned["images"],
            [
                "https://cdn.shopify.com/files/img1.jpg",
                "https://cdn.shopify.com/files/img2.jpg",
            ],
        )

    def test_clean_product_data_list_tags(self):
        product_with_list_tags = dict(self.sample_raw_product)
        product_with_list_tags["tags"] = ["Summer", "Sale", "New"]
        cleaned = clean_product_data(product_with_list_tags)
        self.assertEqual(cleaned["tags"], ["Summer", "Sale", "New"])

    def test_clean_product_data_missing_fields(self):
        cleaned = clean_product_data({"id": 123, "title": "Minimal"})
        self.assertEqual(cleaned["id"], 123)
        self.assertEqual(cleaned["title"], "Minimal")
        self.assertEqual(cleaned["variants"], [])
        self.assertEqual(cleaned["images"], [])
        self.assertEqual(cleaned["tags"], [])

    def test_save_jsonl_and_load_existing_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_products.jsonl"

            records = [
                {"id": 101, "title": "Item 1"},
                {"id": 102, "title": "Item 2"},
            ]

            # Test batch write
            written = save_jsonl_batch(records, file_path=test_file, mode="w")
            self.assertEqual(written, 2)

            # Test appending single record
            saved = save_jsonl({"id": 103, "title": "Item 3"}, file_path=test_file)
            self.assertTrue(saved)

            # Test loading existing IDs
            existing_ids = load_existing_product_ids(test_file)
            self.assertEqual(existing_ids, {101, 102, 103})

            # Verify line count
            with open(test_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            self.assertEqual(len(lines), 3)

    def test_load_existing_ids_with_malformed_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "corrupt_products.jsonl"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write('{"id": 501, "title": "Valid"}\n')
                f.write('NOT_A_VALID_JSON_STRING\n')
                f.write('{"title": "Missing ID"}\n')
                f.write('{"id": 502, "title": "Valid 2"}\n')

            ids = load_existing_product_ids(test_file)
            self.assertEqual(ids, {501, 502})


if __name__ == "__main__":
    unittest.main()
