-- Sales email AI matching schema for PostgreSQL runtime.
-- Raw email bodies and credentials are intentionally not stored.

CREATE TABLE IF NOT EXISTS sales_mailbox_sources (
    id SERIAL PRIMARY KEY,
    source_key VARCHAR(120) NOT NULL UNIQUE,
    display_name VARCHAR(160) NOT NULL,
    source_type VARCHAR(32) NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api')),
    owner_user_id VARCHAR(255),
    retention_days INTEGER NOT NULL DEFAULT 90 CHECK (retention_days BETWEEN 1 AND 365),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales_email_messages (
    id SERIAL PRIMARY KEY,
    mailbox_source_id INTEGER REFERENCES sales_mailbox_sources(id) ON DELETE SET NULL,
    message_id_hash CHAR(64),
    dedupe_key CHAR(64) NOT NULL UNIQUE,
    sender_hash CHAR(64) NOT NULL,
    sender_domain VARCHAR(255),
    normalized_subject VARCHAR(300) NOT NULL,
    received_at TIMESTAMP,
    body_hash CHAR(64) NOT NULL,
    body_excerpt TEXT,
    source_path TEXT,
    source_type VARCHAR(32) NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api')),
    raw_storage_policy VARCHAR(64) NOT NULL DEFAULT 'hash_and_redacted_excerpt_only',
    ingest_status VARCHAR(32) NOT NULL DEFAULT 'new' CHECK (ingest_status IN ('new', 'deduped', 'parsed', 'reviewed', 'rejected', 'error')),
    duplicate_of_id INTEGER REFERENCES sales_email_messages(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (raw_storage_policy = 'hash_and_redacted_excerpt_only')
);

CREATE TABLE IF NOT EXISTS sales_email_entities (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES sales_email_messages(id) ON DELETE CASCADE,
    entity_type VARCHAR(32) NOT NULL CHECK (entity_type IN ('project', 'talent', 'company', 'skill', 'condition', 'other')),
    label VARCHAR(240) NOT NULL,
    normalized_label VARCHAR(240) NOT NULL,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_excerpt TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_requirements (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES sales_email_messages(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    client_or_partner VARCHAR(255),
    summary TEXT,
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    nice_to_have_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    skill_categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    rate_min INTEGER,
    rate_max INTEGER,
    rate_unit VARCHAR(32),
    location VARCHAR(160),
    remote_type VARCHAR(32) CHECK (remote_type IS NULL OR remote_type IN ('onsite', 'hybrid', 'remote', 'unknown')),
    start_date_text VARCHAR(120),
    duration_text VARCHAR(160),
    commercial_flow TEXT,
    restrictions TEXT,
    evidence_excerpt TEXT,
    review_status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'confirmed', 'corrected', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (rate_min IS NULL OR rate_min >= 0),
    CHECK (rate_max IS NULL OR rate_max >= 0),
    CHECK (rate_min IS NULL OR rate_max IS NULL OR rate_min <= rate_max)
);

CREATE TABLE IF NOT EXISTS talent_profiles_from_email (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES sales_email_messages(id) ON DELETE SET NULL,
    anonymized_talent_key VARCHAR(120) NOT NULL UNIQUE,
    summary TEXT,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    skill_categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    experience_years REAL CHECK (experience_years IS NULL OR experience_years >= 0),
    desired_rate_min INTEGER CHECK (desired_rate_min IS NULL OR desired_rate_min >= 0),
    desired_rate_max INTEGER CHECK (desired_rate_max IS NULL OR desired_rate_max >= 0),
    desired_location VARCHAR(160),
    remote_preference VARCHAR(32) CHECK (remote_preference IS NULL OR remote_preference IN ('onsite', 'hybrid', 'remote', 'unknown')),
    availability_text VARCHAR(160),
    evidence_excerpt TEXT,
    review_status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'confirmed', 'corrected', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (desired_rate_min IS NULL OR desired_rate_max IS NULL OR desired_rate_min <= desired_rate_max)
);

CREATE TABLE IF NOT EXISTS requirement_skill_tags (
    id SERIAL PRIMARY KEY,
    project_requirement_id INTEGER REFERENCES project_requirements(id) ON DELETE CASCADE,
    talent_profile_id INTEGER REFERENCES talent_profiles_from_email(id) ON DELETE CASCADE,
    skill_name VARCHAR(120) NOT NULL,
    skill_category VARCHAR(80) NOT NULL DEFAULT 'unknown',
    importance VARCHAR(32) NOT NULL DEFAULT 'required' CHECK (importance IN ('required', 'nice_to_have', 'experience', 'unknown')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_excerpt TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (project_requirement_id IS NOT NULL OR talent_profile_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS email_parse_runs (
    id SERIAL PRIMARY KEY,
    mailbox_source_id INTEGER REFERENCES sales_mailbox_sources(id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    input_count INTEGER NOT NULL DEFAULT 0 CHECK (input_count >= 0),
    unique_count INTEGER NOT NULL DEFAULT 0 CHECK (unique_count >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    parsed_entity_count INTEGER NOT NULL DEFAULT 0 CHECK (parsed_entity_count >= 0),
    model_name VARCHAR(120),
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    error_summary TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_match_results (
    id SERIAL PRIMARY KEY,
    project_requirement_id INTEGER REFERENCES project_requirements(id) ON DELETE CASCADE,
    talent_profile_id INTEGER REFERENCES talent_profiles_from_email(id) ON DELETE CASCADE,
    engineer_id INTEGER REFERENCES engineers(id) ON DELETE SET NULL,
    direction VARCHAR(32) NOT NULL CHECK (direction IN ('engineer_to_project', 'project_to_talent')),
    match_score REAL NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    matched_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    mismatch_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_summary TEXT,
    review_status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'accepted', 'rejected', 'corrected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (project_requirement_id IS NOT NULL OR talent_profile_id IS NOT NULL OR engineer_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS email_match_feedback (
    id SERIAL PRIMARY KEY,
    match_result_id INTEGER NOT NULL REFERENCES email_match_results(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(255),
    feedback_status VARCHAR(32) NOT NULL CHECK (feedback_status IN ('accepted', 'rejected', 'needs_review', 'corrected')),
    corrected_score REAL CHECK (corrected_score IS NULL OR (corrected_score >= 0 AND corrected_score <= 100)),
    corrected_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_email_messages_dedupe_key ON sales_email_messages(dedupe_key);
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_body_hash ON sales_email_messages(body_hash);
CREATE INDEX IF NOT EXISTS idx_sales_email_messages_sender_domain ON sales_email_messages(sender_domain);
CREATE INDEX IF NOT EXISTS idx_sales_email_entities_message_type ON sales_email_entities(message_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_project_requirements_review_status ON project_requirements(review_status);
CREATE INDEX IF NOT EXISTS idx_talent_profiles_review_status ON talent_profiles_from_email(review_status);
CREATE INDEX IF NOT EXISTS idx_requirement_skill_tags_skill ON requirement_skill_tags(skill_name);
CREATE INDEX IF NOT EXISTS idx_email_parse_runs_started_at ON email_parse_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_email_match_results_score ON email_match_results(match_score);

ALTER TABLE sales_mailbox_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_email_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_email_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE talent_profiles_from_email ENABLE ROW LEVEL SECURITY;
ALTER TABLE requirement_skill_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_parse_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_match_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_match_feedback ENABLE ROW LEVEL SECURITY;
