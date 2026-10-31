"""Unit tests for settings and logger configurations."""

import tempfile
import unittest
from pathlib import Path
from config.settings import BASE_DIR, DATA_DIR, LOGS_DIR, RAW_DATA_PATH, PROCESSED_DATA_PATH
from src.logger import setup_logger


class TestSettingsAndLogger(unittest.TestCase):

    def test_paths_are_path_instances_and_absolute(self):
        self.assertIsInstance(BASE_DIR, Path)
        self.assertTrue(BASE_DIR.is_absolute())
        self.assertIsInstance(DATA_DIR, Path)
        self.assertIsInstance(LOGS_DIR, Path)
        self.assertIsInstance(RAW_DATA_PATH, Path)
        self.assertIsInstance(PROCESSED_DATA_PATH, Path)

    def test_setup_logger_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log = Path(tmpdir) / "sub" / "test.log"
            logger = setup_logger(name="TestLoggerUnique", log_file=test_log)
            logger.info("Test message written to log")

            self.assertTrue(test_log.exists())
            with open(test_log, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Test message written to log", content)

            # Close and remove handlers so Windows releases the file handle
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
