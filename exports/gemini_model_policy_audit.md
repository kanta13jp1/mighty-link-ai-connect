# Gemini Model Policy Audit

- Status: `ok`
- Checked at: 2026-09-02
- Production default: `gemini-3.5-flash`
- App default: `gemini-3.5-flash`
- Blockers: 0
- Warnings: 0

## Official Docs Snapshot

- Models: https://ai.google.dev/gemini-api/docs/models
- Context caching: https://ai.google.dev/gemini-api/docs/caching
- Models page last updated UTC: 2026-06-30

## Blockers

No blockers.

## Runtime References

| Path | Line | Model | Severity | Reason |
| --- | ---: | --- | --- | --- |
| src/app.py | 380 | `gemini-3.5-flash` | ok | stable_production_model |
| src/sales_email_parser.py | 13 | `gemini-3.5-flash` | ok | stable_production_model |
| src/structured_ai.py | 104 | `gemini-3.5-flash` | ok | stable_production_model |
| scripts/sync_docs_to_notebooklm.py | 964 | `gemini-3.5-flash` | ok | stable_production_model |

## Current Truth References

| Path | Line | Model | Severity | Reason |
| --- | ---: | --- | --- | --- |
| docs/AI_SAAS_SERVICE_FREEZE_RUNBOOK.md | 36 | `gemini-3.5-flash` | ok | current_truth_reference_allowed |
| docs/AI_SAAS_SERVICE_FREEZE_RUNBOOK.md | 77 | `gemini-3.5-flash` | ok | current_truth_reference_allowed |
| data/WBS.tsv | 194 | `gemini-2.` | ok | current_truth_reference_allowed |
| data/qa_tracker.tsv | 111 | `gemini-3.5-flash` | ok | current_truth_reference_allowed |
| data/qa_tracker.tsv | 119 | `gemini-3.5-flash` | ok | current_truth_reference_allowed |
| data/qa_tracker.tsv | 119 | `gemini-3.1-pro` | ok | current_truth_reference_allowed |
| data/qa_tracker.tsv | 128 | `gemini-3.5-flash` | ok | current_truth_reference_allowed |
