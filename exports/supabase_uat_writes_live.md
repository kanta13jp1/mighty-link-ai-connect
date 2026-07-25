# Supabase UAT DB Write Verification (T845/T921)

- Status: **PASS**
- Mode: `live_transactional_write`
- Live write verified: **True**
- Transaction rolled back: **True**
- Cleanup verified: **True**
- Persisted probe records: `0`
- Summary: Live transactional INSERT/readback passed for 15 tables; ROLLBACK completed and 0 probe records persisted.
- GitHub Actions run: `30149963975`
- Commit: `7d3bcf42ca8e20f03839b4dc766db274712387a1`
- Run URL: https://github.com/kanta13jp1/mighty-link-ai-connect/actions/runs/30149963975

## Tables

- `employee_assessment_responses`: **PASS** (`transactional_insert_readback`)
- `attendance_punch_events`: **PASS** (`transactional_insert_readback`)
- `attendance_timesheet_imports`: **PASS** (`transactional_insert_readback`)
- `usage_analytics_events`: **PASS** (`transactional_insert_readback`)
- `sales_mailbox_sources`: **PASS** (`transactional_insert_readback`)
- `sales_email_messages`: **PASS** (`transactional_insert_readback`)
- `sales_email_entities`: **PASS** (`transactional_insert_readback`)
- `project_requirements`: **PASS** (`transactional_insert_readback`)
- `talent_profiles_from_email`: **PASS** (`transactional_insert_readback`)
- `requirement_skill_tags`: **PASS** (`transactional_insert_readback`)
- `email_parse_runs`: **PASS** (`transactional_insert_readback`)
- `email_match_results`: **PASS** (`transactional_insert_readback`)
- `email_match_feedback`: **PASS** (`transactional_insert_readback`)
- `feedback_events`: **PASS** (`transactional_insert_readback`)
- `support_requests`: **PASS** (`transactional_insert_readback`)

All live probe values are synthetic. Live mode never commits probe rows.
