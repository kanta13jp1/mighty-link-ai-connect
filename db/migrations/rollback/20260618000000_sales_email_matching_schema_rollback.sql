-- Rollback note for 20260618000000_sales_email_matching_schema.
-- Do not run in production until backup/PITR time, Issue approval, and data-loss impact are recorded.
-- Prefer forward-fix migrations unless this schema has not yet received real sales email data.

DROP TABLE IF EXISTS public.email_match_feedback;
DROP TABLE IF EXISTS public.email_match_results;
DROP TABLE IF EXISTS public.email_parse_runs;
DROP TABLE IF EXISTS public.requirement_skill_tags;
DROP TABLE IF EXISTS public.talent_profiles_from_email;
DROP TABLE IF EXISTS public.project_requirements;
DROP TABLE IF EXISTS public.sales_email_entities;
DROP TABLE IF EXISTS public.sales_email_messages;
DROP TABLE IF EXISTS public.sales_mailbox_sources;

-- SQLite/local fallback equivalent, if needed:
-- DROP TABLE IF EXISTS email_match_feedback;
-- DROP TABLE IF EXISTS email_match_results;
-- DROP TABLE IF EXISTS email_parse_runs;
-- DROP TABLE IF EXISTS requirement_skill_tags;
-- DROP TABLE IF EXISTS talent_profiles_from_email;
-- DROP TABLE IF EXISTS project_requirements;
-- DROP TABLE IF EXISTS sales_email_entities;
-- DROP TABLE IF EXISTS sales_email_messages;
-- DROP TABLE IF EXISTS sales_mailbox_sources;
