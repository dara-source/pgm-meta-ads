import importlib.util
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "meta_ads_mcp.py"
SPEC = importlib.util.spec_from_file_location("meta_ads_mcp_env", MODULE_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SERVER)


class EnvLoadingTests(unittest.TestCase):
    def test_existing_environment_wins(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_script = pathlib.Path(temp_dir) / "scripts" / "server.py"
            fake_script.parent.mkdir()
            env_path = pathlib.Path(temp_dir) / ".env"
            env_path.write_text("META_ACCESS_TOKEN=file-token\n", encoding="utf-8")
            with patch.object(SERVER, "__file__", str(fake_script)), patch.dict(os.environ, {"META_ACCESS_TOKEN": "host-token"}, clear=False):
                SERVER._load_local_env()
                self.assertEqual(os.environ["META_ACCESS_TOKEN"], "host-token")


if __name__ == "__main__":
    unittest.main()
