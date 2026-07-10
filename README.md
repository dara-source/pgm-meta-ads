# PGM Meta Ads

A read-only Codex MCP plugin for Meta Ads reporting. It exposes account, creative, demographic, and creative-metadata tools backed by Meta's Marketing API.

## Security model

- Requires only Meta's `ads_read` permission for reporting.
- Reads the token from `META_ACCESS_TOKEN` on the Codex host.
- Contains no tools for creating, editing, pausing, publishing, or deleting ads.
- Never commit `.env` or a Meta token.

## Meta setup

1. Create a business app at Meta for Developers under the PGM business portfolio.
2. Add the Marketing API product.
3. In Meta Business Settings, create or select a system user for reporting.
4. Assign the pilot client's ad account to that system user with read/report access.
5. Generate a system-user token for the PGM app with `ads_read`.
6. Store the token locally in `.env` or a deployment secret store as `META_ACCESS_TOKEN`.

Do not paste the token into ChatGPT, Codex prompts, GitHub issues, or source files.

## Local verification

Copy the example file, then paste the token into the local `.env` file. The real
`.env` is ignored by Git and must never be committed:

```bash
cp .env.example .env
python3 -m unittest discover -s tests -v
```

## Codex plugin configuration

The plugin's `.mcp.json` launches `scripts/meta_ads_mcp.py` over stdio. The Codex host must inherit `META_ACCESS_TOKEN`.

If your local Codex installation does not resolve relative MCP paths from the plugin root, replace the script path in `.mcp.json` with the absolute local path after cloning.

## Included tools

- `list_ad_accounts`
- `get_account_insights`
- `get_creative_performance`
- `get_demographic_breakdown`
- `get_ads_and_creatives`

## Next production step

After the single-client pilot is validated, wrap the same tool layer in a hosted Streamable HTTP MCP service with per-user OAuth, encrypted token storage, tenant isolation, audit logs, and automated token revocation.
