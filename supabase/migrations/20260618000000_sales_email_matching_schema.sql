-- Sales email AI matching schema for Supabase.
-- Raw email bodies and credentials are intentionally not stored.
-- RLS is enabled without anon/authenticated policies; access is via backend service only.

CREATE TABLE IF NOT EXISTS public.sales_mailbox_sources (
    id BIGSERIAL PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL CHECK (char_length(display_name) <= 160),
    source_type TEXT NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api')),
    owner_user_id TEXT,
    retention_days INTEGER NOT NULL DEFAULT 90 CHECK (retention_days BETWEEN 1 AND 365),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.sales_email_messages (
    id BIGSERIAL PRIMARY KEY,
    mailbox_source_id BIGINT REFERENCES public.sales_mailbox_sources(id) ON DELETE SET NULL,
    message_id_hash CHAR(64),
    dedupe_key CHAR(64) NOT NULL UNIQUE,
    sender_hash CHAR(64) NOT NULL,
    sender_domain TEXT CHECK (sender_domain IS NULL OR char_length(sender_domain) <= 255),
    normalized_subject TEXT NOT NULL CHECK (char_length(normalized_subject) <= 300),
    received_at TIMESTAMPTZ,
    body_hash CHAR(64) NOT NULL,
    body_excerpt TEXT CHECK (body_excerpt IS NULL OR char_length(body_excerpt) <= 1000),
    source_path TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api')),
    raw_storage_policy TEXT NOT NULL DEFAULT 'hash_and_redacted_excerpt_only',
    ingest_status TEXT NOT NULL DEFAULT 'new' CHECK (ingest_status IN ('new', 'deduped', 'parsed', 'reviewed', 'rejected', 'error')),
    duplicate_of_id BIGINT REFERENCES public.sales_email_messages(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (raw_storage_policy = 'hash_and_redacted_excerpt_only')
);

CREATE TABLE IF NOT EXISTS public.sales_email_entities (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES public.sales_email_messages(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('project', 'talent', 'company', 'skill', 'condition', 'other')),
    label TEXT NOT NULL CHECK (char_length(label) <= 240),
    normalized_label TEXT NOT NULL CHECK (char_length(normalized_label) <= 240),
    confidence NUMERIC(4, 3) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_excerpt TEXT CHECK (evidence_excerpt IS NULL OR char_length(evidence_excerpt) <= 1000),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.project_requirements (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT REFERENCES public.sales_email_messages(id) ON DELETE SET NULL,
    title TEXT NOT NULL CHECK (char_length(title) <= 255),
    client_or_partner TEXT CHECK (client_or_partner IS NULL OR char_length(client_or_partner) <= 255),
    summary TEXT,
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    nice_to_have_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    skill_categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    rate_min INTEGER CHECK (rate_min IS NULL OR rate_min >= 0),
    rate_max INTEGER CHECK (rate_max IS NULL OR rate_max >= 0),
    rate_unit TEXT,
    location TEXT CHECK (location IS NULL OR char_length(location) <= 160),
    remote_type TEXT CHECK (remote_type IS NULL OR remote_type IN ('onsite', 'hybrid', 'remote', 'unknown')),
    start_date_text TEXT CHECK (start_date_text IS NULL OR char_length(start_date_text) <= 120),
    duration_text TEXT CHECK (duration_text IS NULL OR char_length(duration_text) <= 160),
    commercial_flow TEXT,
    restrictions TEXT,
    evidence_excerpt TEXT CHECK (evidence_excerpt IS NULL OR char_length(evidence_excerpt) <= 1000),
    review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'confirmed', 'corrected', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (rate_min IS NULL OR rate_max IS NULL OR rate_min <= rate_max)
);

CREATE TABLE IF NOT EXISTS public.talent_profiles_from_email (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT REFERENCES public.sales_email_messages(id) ON DELETE SET NULL,
    anonymized_talent_key TEXT NOT NULL UNIQUE CHECK (char_length(anonymized_talent_key) <= 120),
    summary TEXT,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    skill_categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    experience_years NUMERIC(4, 1) CHECK (experience_years IS NULL OR experience_years >= 0),
    desired_rate_min INTEGER CHECK (desired_rate_min IS NULL OR desired_rate_min >= 0),
    desired_rate_max INTEGER CHECK (desired_rate_max IS NULL OR desired_rate_max >= 0),
    desired_location TEXT CHECK (desired_location IS NULL OR char_length(desired_location) <= 160),
    remote_preference TEXT CHECK (remote_preference IS NULL OR remote_preference IN ('onsite', 'hybrid', 'remote', 'unknown')),
    availability_text TEXT CHECK (availability_text IS NULL OR char_length(availability_text) <= 160),
    evidence_excerpt TEXT CHECK (evidence_excerpt IS NULL OR char_length(evidence_excerpt) <= 1000),
    review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'confirmed', 'corrected', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (desired_rate_min IS NULL OR desired_rate_max IS NULL OR desired_rate_min <= desired_rate_max)
);

CREATE TABLE IF NOT EXISTS public.requirement_skill_tags (
    id BIGSERIAL PRIMARY KEY,
    project_requirement_id BIGINT REFERENCES public.project_requirements(id) ON DELETE CASCADE,
    talent_profile_id BIGINT REFERENCES public.talent_profiles_from_email(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL CHECK (char_length(skill_name) <= 120),
    skill_category TEXT NOT NULL DEFAULT 'unknown' CHECK (char_length(skill_category) <= 80),
    importance TEXT NOT NULL DEFAULT 'required' CHECK (importance IN ('required', 'nice_to_have', 'experience', 'unknown')),
    confidence NUMERIC(4, 3) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_excerpt TEXT CHECK (evidence_excerpt IS NULL OR char_length(evidence_excerpt) <= 1000),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (project_requirement_id IS NOT NULL OR talent_profile_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS public.email_parse_runs (
    id BIGSERIAL PRIMARY KEY,
    mailbox_source_id BIGINT REFERENCES public.sales_mailbox_sources(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    input_count INTEGER NOT NULL DEFAULT 0 CHECK (input_count >= 0),
    unique_count INTEGER NOT NULL DEFAULT 0 CHECK (unique_count >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    parsed_entity_count INTEGER NOT NULL DEFAULT 0 CHECK (parsed_entity_count >= 0),
    model_name TEXT CHECK (model_name IS NULL OR char_length(model_name) <= 120),
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    error_summary TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.email_match_results (
    id BIGSERIAL PRIMARY KEY,
    project_requirement_id BIGINT REFERENCES public.project_requirements(id) ON DELETE CASCADE,
    talent_profile_id BIGINT REFERENCES public.talent_profiles_from_email(id) ON DELETE CASCADE,
    engineer_id INTEGER,
    direction TEXT NOT NULL CHECK (direction IN ('engineer_to_project', 'project_to_talent')),
    match_score NUMERIC(5, 2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    matched_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    mismatch_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_summary TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'accepted', 'rejected', 'corrected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (project_requirement_id IS NOT NULL OR talent_profile_id IS NOT NULL OR engineer_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS public.email_match_feedback (
    id BIGSERIAL PRIMARY KEY,
    match_result_id BIGINT NOT NULL REFERENCES public.email_match_results(id) ON DELETE CASCADE,
    reviewer_id TEXT CHECK (reviewer_id IS NULL OR char_length(reviewer_id) <= 255),
    feedback_status TEXT NOT NULL CHECK (feedback_status IN ('accepted', 'rejected', 'needs_review', 'corrected')),
    corrected_score NUMERIC(5, 2) CHECK (corrected_score IS NULL OR (corrected_score >= 0 AND corrected_score <= 100)),
    corrected_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sales_email_messages_dedupe_key
    ON public.sales_email_messages(dedupe_key);
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_body_hash
    ON public.sales_email_messages(body_hash);
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_sender_domain
    ON public.sales_email_messages(sender_domain);
CREATE INDEX IF NOT EXISTS idx_sales_email_entities_message_type
    ON public.sales_email_entities(message_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_project_requirements_review_status
    ON public.project_requirements(review_status);
CREATE INDEX IF NOT EXISTS idx_project_requirements_required_skills_gin
    ON public.project_requirements USING gin (required_skills);
CREATE INDEX IF NOT EXISTS idx_talent_profiles_review_status
    ON public.talent_profiles_from_email(review_status);
CREATE INDEX IF NOT EXISTS idx_talent_profiles_skills_gin
    ON public.talent_profiles_from_email USING gin (skills);
CREATE INDEX IF NOT EXISTS idx_requirement_skill_tags_skill
    ON public.requirement_skill_tags(lower(skill_name));
CREATE INDEX IF NOT EXISTS idx_email_parse_runs_started_at
    ON public.email_parse_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_match_results_score
    ON public.email_match_results(match_score DESC);

CREATE TRIGGER set_timestamp_sales_mailbox_sources
BEFORE UPDATE ON public.sales_mailbox_sources
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_sales_email_messages
BEFORE UPDATE ON public.sales_email_messages
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_project_requirements
BEFORE UPDATE ON public.project_requirements
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_talent_profiles_from_email
BEFORE UPDATE ON public.talent_profiles_from_email
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_email_match_results
BEFORE UPDATE ON public.email_match_results
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

ALTER TABLE public.sales_mailbox_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales_email_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales_email_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.talent_profiles_from_email ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.requirement_skill_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_parse_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_match_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_match_feedback ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.sales_mailbox_sources FROM anon, authenticated;
REVOKE ALL ON TABLE public.sales_email_messages FROM anon, authenticated;
REVOKE ALL ON TABLE public.sales_email_entities FROM anon, authenticated;
REVOKE ALL ON TABLE public.project_requirements FROM anon, authenticated;
REVOKE ALL ON TABLE public.talent_profiles_from_email FROM anon, authenticated;
REVOKE ALL ON TABLE public.requirement_skill_tags FROM anon, authenticated;
REVOKE ALL ON TABLE public.email_parse_runs FROM anon, authenticated;
REVOKE ALL ON TABLE public.email_match_results FROM anon, authenticated;
REVOKE ALL ON TABLE public.email_match_feedback FROM anon, authenticated;
