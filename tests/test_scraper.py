"""Unit tests for the single-product scraper."""

import unittest
from unittest.mock import MagicMock, patch
import httpx
from src.scraper import fetch_product_by_handle


class TestScraper(unittest.TestCase):

    @patch("httpx.Client.get")
    def test_fetch_product_by_handle_success(self, mock_get):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "product": {
                "id": 888222,
                "title": "Mock Dungaree",
                "handle": "mock-dungaree",
            }
        }
        mock_get.return_value = mock_response

        product = fetch_product_by_handle("mock-dungaree")
        self.assertIsNotNone(product)
        self.assertEqual(product["id"], 888222)
        self.assertEqual(product["title"], "Mock Dungaree")

    @patch("httpx.Client.get")
    def test_fetch_product_by_handle_not_found(self, mock_get):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        product = fetch_product_by_handle("non-existent-product")
        self.assertIsNone(product)


if __name__ == "__main__":
    unittest.main()
