# Supabase Query Performance Review

- Task: T761
- Generated: 2026-06-14T19:06:40Z
- Overall status: ready

## Summary

| Status | Count |
| --- | ---: |
| ok | 1 |
| ready | 3 |
| warning | 0 |
| critical | 0 |

## Dashboard Checklist

| Area | Action | Decision Rule |
| --- | --- | --- |
| Query Performance | Open Supabase Dashboard > Database > Query Performance and sort by total time, mean time, and calls. | Map the top slow queries to API route or UI operation before changing indexes. |
| Performance Advisor | Open Database > Performance Advisor and rerun checks after fixes. | Create a GitHub Issue for every warning that affects production reads, writes, locks, or bloat. |
| Index Advisor | For each slow query, open the Indexes tab and compare suggested indexes with existing indexes. | Accept only recommendations backed by EXPLAIN evidence and expected production query shape. |
| SQL / Inspect | Run supabase inspect db outliers, index-usage, unused-indexes, seq-scans, cache-hit, locks, and blocking. | Use the CLI output to validate Dashboard findings and avoid one-off UI-only decisions. |
| Migration | Record accepted DDL as a forward migration and prefer CREATE INDEX CONCURRENTLY for production-sized tables. | Never apply index DDL directly in production without WBS, Issue, rollback note, and staging evidence. |

## Generated Checks

| Key | Status | Source | Action | Evidence |
| --- | --- | --- | --- | --- |
| diagnostic_report_status | ready | exports/supabase_performance_report.json | Use this dry-run bundle for the next live Supabase Dashboard review. | status=planned, dry_run=True, probes=7, api_results=0 |
| diagnostic_probe_coverage | ok | exports/supabase_performance_report.json | Keep the diagnostic bundle aligned with Supabase pg_stat_statements and index review needs. | missing=none |
| dashboard_review_gate | ready | Supabase Dashboard | Run Query Performance, Performance Advisor, and Index Advisor review before any production index migration. | manual dashboard confirmation required; no production credentials stored in this artifact |
| migration_safety_gate | ready | DB_MIGRATION_MANAGEMENT_RUNBOOK.md | Use forward migrations, staging verification, and CREATE INDEX CONCURRENTLY where applicable. | direct production DDL is disallowed by project operating rules |

## Supabase Inspect Commands

- `supabase inspect db outliers`
- `supabase inspect db index-usage`
- `supabase inspect db unused-indexes`
- `supabase inspect db seq-scans`
- `supabase inspect db cache-hit`
- `supabase inspect db locks`
- `supabase inspect db blocking`

## Tuning Rules

- Do not add or drop indexes from a single slow-query observation.
- Prefer measured query plans from staging and production-like data volume.
- Create or update a GitHub Issue before accepted DDL work.
- Write accepted index DDL as a forward migration and include rollback notes.
- Review unused indexes across at least two reporting cycles before dropping them.
