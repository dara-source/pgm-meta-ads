---
name: meta-reporting
description: Use PGM's read-only Meta Ads tools to analyze account performance, rank creatives, compare sources, and prepare monthly client reporting.
---

# PGM Meta Reporting

Use the `pgm-meta-ads` MCP tools only for read-only reporting.

## Workflow

1. Call `list_ad_accounts` and verify the account name and ID before analysis.
2. Confirm the reporting window, attribution convention, primary KPI, and minimum-spend threshold.
3. Use `get_account_insights` for deterministic account and monthly comparisons.
4. Use `get_creative_performance` for ad-level ranking. Do not call an ad a winner unless it clears the agreed spend threshold.
5. Use `get_ads_and_creatives` to join ad IDs to previews, creation times, and current Meta status.
6. Treat first spend/impression date as launch date when daily insights are available; do not assume Meta `created_time` equals launch.
7. Use `get_demographic_breakdown` only when the sample is material and the finding is actionable.
8. Never claim Meta knows which agency made an asset. Join ad IDs/names to the PGM source mapping in Notion or the reporting data layer.
9. Distinguish facts, deterministic calculations, and hypotheses in every report.

## Safety

- Never request or display an access token.
- Never add write permissions or tools that create, edit, pause, publish, or delete ads.
- If Meta returns a permission error, report the missing permission without asking the user to paste credentials into chat.
