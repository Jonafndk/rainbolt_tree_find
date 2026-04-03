import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from place_finder_ai.cli import _extract_seed_queries


class CliSeedTests(unittest.TestCase):
    def test_extract_seed_queries(self):
        seeds = _extract_seed_queries("park bench near Lakeview")
        self.assertIn("public park", seeds)

    def test_fallback_seed(self):
        seeds = _extract_seed_queries("no location clues")
        self.assertEqual(seeds, ["family park"])


if __name__ == "__main__":
    unittest.main()
