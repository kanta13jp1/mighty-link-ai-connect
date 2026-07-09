-- 20260709000000_fk_covering_indexes.sql
-- T881: covering btree indexes for foreign-key columns.
--
-- PostgreSQL auto-creates indexes only for PRIMARY KEY / UNIQUE constraints,
-- never for foreign-key columns. Supabase's Database Performance Advisor flags
-- "unindexed foreign keys" because joins on them fall back to sequential scans
-- and, more importantly for this project, ON DELETE CASCADE / SET NULL parent
-- deletes must full-scan every referencing child table (data-retention/deletion
-- flow, T847).
--
-- This migration is additive and idempotent (CREATE INDEX IF NOT EXISTS on
-- single plain columns). All target tables are small/new, so a plain (in-txn)
-- CREATE INDEX is safe here. For a large, high-write table prefer
-- CREATE INDEX CONCURRENTLY run OUTSIDE a transaction (see
-- docs/PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md).
-- Verified by scripts/audit_fk_index_coverage.py (gap count -> 0).

-- Core diagnosis: audits.match_id -> matches(id) ON DELETE SET NULL
CREATE INDEX IF NOT EXISTS idx_audits_match_id
    ON public.audits (match_id);

-- Sales-email matching schema (the actively-joined domain)
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_mailbox_source_id
    ON public.sales_email_messages (mailbox_source_id);
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_duplicate_of_id
    ON public.sales_email_messages (duplicate_of_id);
CREATE INDEX IF NOT EXISTS idx_project_requirements_message_id
    ON public.project_requirements (message_id);
CREATE INDEX IF NOT EXISTS idx_talent_profiles_from_email_message_id
    ON public.talent_profiles_from_email (message_id);
CREATE INDEX IF NOT EXISTS idx_requirement_skill_tags_project_requirement_id
    ON public.requirement_skill_tags (project_requirement_id);
CREATE INDEX IF NOT EXISTS idx_requirement_skill_tags_talent_profile_id
    ON public.requirement_skill_tags (talent_profile_id);
CREATE INDEX IF NOT EXISTS idx_email_parse_runs_mailbox_source_id
    ON public.email_parse_runs (mailbox_source_id);
CREATE INDEX IF NOT EXISTS idx_email_match_results_project_requirement_id
    ON public.email_match_results (project_requirement_id);
CREATE INDEX IF NOT EXISTS idx_email_match_results_talent_profile_id
    ON public.email_match_results (talent_profile_id);
CREATE INDEX IF NOT EXISTS idx_email_match_feedback_match_result_id
    ON public.email_match_feedback (match_result_id);
