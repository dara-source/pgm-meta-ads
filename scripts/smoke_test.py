#!/usr/bin/env python3
"""Confirm the local Meta token can list assigned ad accounts."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys


SERVER_PATH = pathlib.Path(__file__).with_name("meta_ads_mcp.py")
SPEC = importlib.util.spec_from_file_location("pgm_meta_ads_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SERVER)


def main() -> int:
    try:
        accounts = SERVER.call_tool("list_ad_accounts", {"limit": 100})
    except Exception as exc:  # The smoke test should render the API error cleanly.
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1

    safe_accounts = [
        {
            "id": account.get("id"),
            "name": account.get("name"),
            "account_status": account.get("account_status"),
            "currency": account.get("currency"),
            "timezone_name": account.get("timezone_name"),
        }
        for account in accounts
    ]
    print(json.dumps(safe_accounts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
