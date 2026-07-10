import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "meta_ads_mcp.py"
SPEC = importlib.util.spec_from_file_location("meta_ads_mcp", MODULE_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SERVER)


class ServerTests(unittest.TestCase):
    def test_account_id_normalization(self):
        self.assertEqual(SERVER._account_id("123"), "act_123")
        self.assertEqual(SERVER._account_id("act_123"), "act_123")

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            SERVER._date_range({"since": "2026-07-10", "until": "2026-07-01"})

    def test_tool_names_are_unique(self):
        names = [tool["name"] for tool in SERVER.TOOLS]
        self.assertEqual(len(names), len(set(names)))

    def test_creative_filters(self):
        rows = [
            {"ad_name": "PGM-NUT-C001-V01", "spend": "125"},
            {"ad_name": "Internal-Concept", "spend": "400"},
            {"ad_name": "PGM-NUT-C002-V01", "spend": "25"},
        ]
        with patch.object(SERVER, "_all_pages", return_value=rows), patch.object(SERVER, "_token", return_value="test"):
            result = SERVER.call_tool("get_creative_performance", {
                "ad_account_id": "123",
                "since": "2026-06-01",
                "until": "2026-06-30",
                "name_contains": "PGM-",
                "minimum_spend": 100,
            })
        self.assertEqual(result, [rows[0]])

    def test_initialize_protocol(self):
        self.assertEqual(SERVER.SERVER_NAME, "pgm-meta-ads")
        json.dumps(SERVER.TOOLS)


if __name__ == "__main__":
    unittest.main()
