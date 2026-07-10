#!/usr/bin/env python3
"""Read-only Meta Ads MCP server for Point Guard Media.

The server intentionally exposes no create, update, pause, publish, or delete
operations. It reads a Meta access token from META_ACCESS_TOKEN at runtime.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any


def _load_local_env() -> None:
    """Load a git-ignored .env file from the plugin root when present."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env()

SERVER_NAME = "pgm-meta-ads"
SERVER_VERSION = "0.1.0"
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v25.0")
GRAPH_ROOT = f"https://graph.facebook.com/{GRAPH_VERSION}"


class MetaAPIError(RuntimeError):
    pass


def _token() -> str:
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    if not token:
        raise MetaAPIError(
            "META_ACCESS_TOKEN is not configured. Set a read-only token with "
            "the ads_read permission in the Codex host environment."
        )
    return token


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = dict(params or {})
    query["access_token"] = _token()
    url = f"{GRAPH_ROOT}/{path.lstrip('/')}?{urllib.parse.urlencode(query, doseq=True)}"
    request = urllib.request.Request(url, headers={"User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
            detail = payload.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            detail = body
        raise MetaAPIError(f"Meta API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MetaAPIError(f"Could not reach Meta Graph API: {exc.reason}") from exc


def _all_pages(path: str, params: dict[str, Any], max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    payload = _get(path, params)
    while True:
        rows.extend(payload.get("data", []))
        if len(rows) >= max_rows:
            return rows[:max_rows]
        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            return rows
        request = urllib.request.Request(next_url, headers={"User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise MetaAPIError(f"Meta pagination failed: {exc}") from exc


def _date_range(arguments: dict[str, Any], default_days: int = 30) -> tuple[str, str]:
    until = arguments.get("until") or date.today().isoformat()
    since = arguments.get("since") or (date.fromisoformat(until) - timedelta(days=default_days - 1)).isoformat()
    if date.fromisoformat(since) > date.fromisoformat(until):
        raise ValueError("since must be on or before until")
    return since, until


def _account_id(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("ad_account_id is required")
    return cleaned if cleaned.startswith("act_") else f"act_{cleaned}"


INSIGHT_FIELDS = [
    "account_id", "account_name", "campaign_id", "campaign_name", "adset_id",
    "adset_name", "ad_id", "ad_name", "spend", "impressions", "reach",
    "frequency", "clicks", "inline_link_clicks", "outbound_clicks", "ctr",
    "cpc", "cpm", "actions", "action_values", "cost_per_action_type",
    "video_play_actions", "video_p25_watched_actions", "video_p50_watched_actions",
    "video_p75_watched_actions", "video_p100_watched_actions", "date_start", "date_stop",
]


TOOLS = [
    {
        "name": "list_ad_accounts",
        "description": "List Meta ad accounts accessible to the configured read-only token.",
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 100}}},
    },
    {
        "name": "get_account_insights",
        "description": "Get account, campaign, ad set, or ad-level Meta performance for a date range.",
        "inputSchema": {
            "type": "object",
            "required": ["ad_account_id"],
            "properties": {
                "ad_account_id": {"type": "string"},
                "since": {"type": "string", "format": "date"},
                "until": {"type": "string", "format": "date"},
                "level": {"type": "string", "enum": ["account", "campaign", "adset", "ad"], "default": "account"},
                "time_increment": {"oneOf": [{"type": "integer", "minimum": 1, "maximum": 90}, {"type": "string", "enum": ["monthly"]}], "default": "monthly"},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 1000},
            },
        },
    },
    {
        "name": "get_creative_performance",
        "description": "Get ad-level performance for ranking and qualifying creatives, optionally filtered by an ad-name code such as PGM-.",
        "inputSchema": {
            "type": "object",
            "required": ["ad_account_id"],
            "properties": {
                "ad_account_id": {"type": "string"},
                "since": {"type": "string", "format": "date"},
                "until": {"type": "string", "format": "date"},
                "name_contains": {"type": "string"},
                "minimum_spend": {"type": "number", "minimum": 0, "default": 0},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 1000},
            },
        },
    },
    {
        "name": "get_demographic_breakdown",
        "description": "Get Meta ad performance broken down by age and gender.",
        "inputSchema": {
            "type": "object",
            "required": ["ad_account_id"],
            "properties": {
                "ad_account_id": {"type": "string"},
                "since": {"type": "string", "format": "date"},
                "until": {"type": "string", "format": "date"},
                "level": {"type": "string", "enum": ["account", "campaign", "adset", "ad"], "default": "account"},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 1000},
            },
        },
    },
    {
        "name": "get_ads_and_creatives",
        "description": "Get ad status, creation time, and creative metadata including thumbnails for reporting.",
        "inputSchema": {
            "type": "object",
            "required": ["ad_account_id"],
            "properties": {
                "ad_account_id": {"type": "string"},
                "effective_status": {"type": "array", "items": {"type": "string"}, "default": ["ACTIVE"]},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 1000},
            },
        },
    },
]


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "list_ad_accounts":
        return _all_pages("me/adaccounts", {"fields": "id,name,account_status,currency,timezone_name,business", "limit": min(arguments.get("limit", 100), 200)}, arguments.get("limit", 100))

    account = _account_id(arguments.get("ad_account_id", ""))
    since, until = _date_range(arguments)

    if name == "get_account_insights":
        max_rows = arguments.get("max_rows", 1000)
        params = {
            "fields": ",".join(INSIGHT_FIELDS),
            "level": arguments.get("level", "account"),
            "time_range": json.dumps({"since": since, "until": until}),
            "time_increment": arguments.get("time_increment", "monthly"),
            "limit": min(max_rows, 500),
        }
        return _all_pages(f"{account}/insights", params, max_rows)

    if name == "get_creative_performance":
        max_rows = arguments.get("max_rows", 1000)
        params = {
            "fields": ",".join(INSIGHT_FIELDS),
            "level": "ad",
            "time_range": json.dumps({"since": since, "until": until}),
            "time_increment": 1,
            "limit": min(max_rows, 500),
        }
        rows = _all_pages(f"{account}/insights", params, max_rows)
        needle = arguments.get("name_contains", "").casefold()
        minimum_spend = float(arguments.get("minimum_spend", 0))
        return [row for row in rows if float(row.get("spend", 0) or 0) >= minimum_spend and (not needle or needle in row.get("ad_name", "").casefold())]

    if name == "get_demographic_breakdown":
        max_rows = arguments.get("max_rows", 1000)
        params = {
            "fields": ",".join(INSIGHT_FIELDS),
            "level": arguments.get("level", "account"),
            "breakdowns": "age,gender",
            "time_range": json.dumps({"since": since, "until": until}),
            "limit": min(max_rows, 500),
        }
        return _all_pages(f"{account}/insights", params, max_rows)

    if name == "get_ads_and_creatives":
        max_rows = arguments.get("max_rows", 1000)
        statuses = arguments.get("effective_status", ["ACTIVE"])
        params = {
            "fields": "id,name,status,effective_status,created_time,updated_time,creative{id,name,title,body,thumbnail_url,image_url,object_story_spec,asset_feed_spec}",
            "effective_status": json.dumps(statuses),
            "limit": min(max_rows, 500),
        }
        return _all_pages(f"{account}/ads", params, max_rows)

    raise ValueError(f"Unknown tool: {name}")


def _reply(request_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def handle(message: dict[str, Any]) -> None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return
    try:
        if method == "initialize":
            _reply(request_id, {
                "protocolVersion": message.get("params", {}).get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        elif method == "ping":
            _reply(request_id, {})
        elif method == "tools/list":
            _reply(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = message.get("params", {})
            result = call_tool(params.get("name", ""), params.get("arguments", {}))
            _reply(request_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False})
        else:
            _reply(request_id, error={"code": -32601, "message": f"Method not found: {method}"})
    except (MetaAPIError, ValueError, TypeError) as exc:
        if method == "tools/call":
            _reply(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        else:
            _reply(request_id, error={"code": -32602, "message": str(exc)})


def main() -> None:
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(message)


if __name__ == "__main__":
    main()
