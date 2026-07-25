# Supabase UAT DB Write Verification (T845/T921)

- Status: **PASS**
- Mode: `offline_schema_contract`
- Live write verified: **False**
- Transaction rolled back: **False**
- Cleanup verified: **False**
- Persisted probe records: `None`
- Summary: Offline schema contract passed for 15 UAT tables. This does not claim a live database write.

## Tables

- `employee_assessment_responses`: **PASS** (`migration_contract`)
- `attendance_punch_events`: **PASS** (`migration_contract`)
- `attendance_timesheet_imports`: **PASS** (`migration_contract`)
- `usage_analytics_events`: **PASS** (`migration_contract`)
- `sales_mailbox_sources`: **PASS** (`migration_contract`)
- `sales_email_messages`: **PASS** (`migration_contract`)
- `sales_email_entities`: **PASS** (`migration_contract`)
- `project_requirements`: **PASS** (`migration_contract`)
- `talent_profiles_from_email`: **PASS** (`migration_contract`)
- `requirement_skill_tags`: **PASS** (`migration_contract`)
- `email_parse_runs`: **PASS** (`migration_contract`)
- `email_match_results`: **PASS** (`migration_contract`)
- `email_match_feedback`: **PASS** (`migration_contract`)
- `feedback_events`: **PASS** (`migration_contract`)
- `support_requests`: **PASS** (`migration_contract`)

All live probe values are synthetic. Live mode never commits probe rows.
