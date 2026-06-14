# Weekly Cost Allocation Dashboard

- Task: T757
- Generated: 2026-06-14T19:06:32Z
- Period: 2026-06-09 to 2026-06-15
- Overall status: unknown

## Summary

| Metric | Value |
| --- | ---: |
| Weekly actual total | $0.00 |
| Billable events | 0 |
| Blocked events | 47 |
| Critical centers | 0 |
| Warning centers | 0 |
| Unknown actual centers | 7 |

## Cost Centers

| Cost center | Owner | Status | Weekly actual | Monthly budget | Billable | Blocked | Source |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| ai_api_gemini | Antigravity + Gemini | unknown | unknown | $20.00 | 0 | 0 | data/external_api_usage.jsonl; Google AI Studio usage; Cloud Billing export |
| ai_api_seedance | Antigravity + Gemini | unknown | unknown | $20.00 | 0 | 47 | data/external_api_usage.jsonl; BytePlus ModelArk monitoring |
| firebase_google_cloud | VSCode + Codex | unknown | unknown | $10.00 | 0 | 0 | Cloud Billing BigQuery export; Firebase budgets |
| github_actions | VSCode + Codex | unknown | unknown | $10.00 | 0 | 0 | GitHub Actions usage |
| slack_notifications | VSCode + Codex | unknown | unknown | $0.00 | 0 | 0 | Slack incoming webhook / chat.postMessage |
| stripe_billing | VSCode + Codex | unknown | unknown | $5.00 | 0 | 0 | Stripe Billing Meters; Stripe Dashboard |
| supabase_db | VSCode + Codex | unknown | unknown | $25.00 | 0 | 0 | Supabase dashboard; Supabase Management API |

## Notification

- Email draft: `exports/weekly_cost_alert_email.md`
- Slack payload draft: `exports/weekly_cost_slack_payload.json`

## Notes

- Provider consoles, Cloud Billing export, Supabase billing, and Stripe Dashboard remain the source of truth for billed amounts.
- Missing actuals are intentionally shown as `unknown`; do not invent spend from local logs.
- Notification secrets are read from environment variables only and are not written to artifacts.
