-- Supabase local development seed data.
-- Keep this file synthetic only. Do not copy production or personal data here.

INSERT INTO public.profiles (user_id, name, email, resume_profile)
VALUES
  (
    'local_user_001',
    'Local Engineer Alpha',
    'alpha.local@example.test',
    '{
      "title": "Senior AI application engineer",
      "skills": ["Python", "FastAPI", "PostgreSQL", "Firebase", "Supabase", "Docker"],
      "experience_years": 8,
      "recent_project": "Built a local-only matching API test harness"
    }'::jsonb
  ),
  (
    'local_user_002',
    'Local Engineer Beta',
    'beta.local@example.test',
    '{
      "title": "Frontend application engineer",
      "skills": ["HTML", "CSS", "JavaScript", "Accessibility", "Git"],
      "experience_years": 3,
      "recent_project": "Implemented a public demo quality checklist"
    }'::jsonb
  )
ON CONFLICT (user_id) DO UPDATE
SET
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  resume_profile = EXCLUDED.resume_profile;

INSERT INTO public.matches (user_id, project_id, fit_score, score_details, matched_skills, missing_skills)
VALUES
  (
    'local_user_001',
    'local_project_alpha',
    91.50,
    '{
      "technical_score": 93,
      "experience_score": 90,
      "fit_factor_4axis": {
        "skill_alignment": 94,
        "architecture_understanding": 91,
        "best_practices": 90,
        "security_compliance": 91
      },
      "gap_analysis": "Strong local-only backend and database fit."
    }'::jsonb,
    ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Firebase', 'Supabase'],
    ARRAY['Kubernetes']
  ),
  (
    'local_user_002',
    'local_project_beta',
    78.00,
    '{
      "technical_score": 80,
      "experience_score": 76,
      "fit_factor_4axis": {
        "skill_alignment": 82,
        "architecture_understanding": 75,
        "best_practices": 78,
        "security_compliance": 77
      },
      "gap_analysis": "Good frontend fit with backend onboarding recommended."
    }'::jsonb,
    ARRAY['HTML', 'CSS', 'JavaScript', 'Accessibility'],
    ARRAY['Python', 'Supabase']
  )
ON CONFLICT DO NOTHING;

INSERT INTO public.audits (match_id, prompt_version, raw_prompt, raw_response, tokens_used)
SELECT
  id,
  'local-seed-v1',
  'Synthetic local prompt for emulator stack verification.',
  '{"fit_score": 91.5, "mode": "local_seed"}',
  512
FROM public.matches
WHERE project_id = 'local_project_alpha'
LIMIT 1;

INSERT INTO public.usage_ledgers (user_id, daily_calls_count, daily_tokens_count, limit_exceeded, reset_at)
VALUES
  (
    'local_user_001',
    2,
    1200,
    FALSE,
    timezone('utc'::text, now()) + interval '1 day'
  ),
  (
    'local_user_002',
    0,
    0,
    FALSE,
    timezone('utc'::text, now()) + interval '1 day'
  )
ON CONFLICT (user_id) DO UPDATE
SET
  daily_calls_count = EXCLUDED.daily_calls_count,
  daily_tokens_count = EXCLUDED.daily_tokens_count,
  limit_exceeded = EXCLUDED.limit_exceeded,
  reset_at = EXCLUDED.reset_at;

WITH source AS (
  INSERT INTO public.sales_mailbox_sources (
    source_key,
    display_name,
    source_type,
    retention_days,
    metadata
  )
  VALUES (
    'local_synthetic_sales_mailbox',
    'Local synthetic sales mailbox',
    'manual_upload',
    30,
    '{"seed": true, "contains_real_mail": false}'::jsonb
  )
  ON CONFLICT (source_key) DO UPDATE
  SET
    display_name = EXCLUDED.display_name,
    source_type = EXCLUDED.source_type,
    retention_days = EXCLUDED.retention_days,
    metadata = EXCLUDED.metadata
  RETURNING id
),
project_message AS (
  INSERT INTO public.sales_email_messages (
    mailbox_source_id,
    message_id_hash,
    dedupe_key,
    sender_hash,
    sender_domain,
    normalized_subject,
    received_at,
    body_hash,
    body_excerpt,
    source_path,
    source_type,
    ingest_status,
    metadata
  )
  SELECT
    id,
    repeat('1', 64),
    repeat('2', 64),
    repeat('3', 64),
    'example.test',
    'Synthetic SQL Oracle remote project',
    timezone('utc'::text, now()),
    repeat('4', 64),
    'Synthetic project mail. Contact fields are redacted before storage.',
    'supabase/seed.sql#project',
    'manual_upload',
    'parsed',
    '{"seed": true}'::jsonb
  FROM source
  ON CONFLICT (dedupe_key) DO UPDATE
  SET
    ingest_status = EXCLUDED.ingest_status,
    body_excerpt = EXCLUDED.body_excerpt,
    metadata = EXCLUDED.metadata
  RETURNING id
),
talent_message AS (
  INSERT INTO public.sales_email_messages (
    mailbox_source_id,
    message_id_hash,
    dedupe_key,
    sender_hash,
    sender_domain,
    normalized_subject,
    received_at,
    body_hash,
    body_excerpt,
    source_path,
    source_type,
    ingest_status,
    metadata
  )
  SELECT
    id,
    repeat('5', 64),
    repeat('6', 64),
    repeat('7', 64),
    'example.test',
    'Synthetic Java AWS talent proposal',
    timezone('utc'::text, now()),
    repeat('8', 64),
    'Synthetic talent mail. Contact fields are redacted before storage.',
    'supabase/seed.sql#talent',
    'manual_upload',
    'parsed',
    '{"seed": true}'::jsonb
  FROM source
  ON CONFLICT (dedupe_key) DO UPDATE
  SET
    ingest_status = EXCLUDED.ingest_status,
    body_excerpt = EXCLUDED.body_excerpt,
    metadata = EXCLUDED.metadata
  RETURNING id
),
project_row AS (
  INSERT INTO public.project_requirements (
    message_id,
    title,
    summary,
    required_skills,
    nice_to_have_skills,
    skill_categories,
    rate_min,
    rate_max,
    rate_unit,
    location,
    remote_type,
    start_date_text,
    duration_text,
    evidence_excerpt,
    review_status,
    metadata
  )
  SELECT
    id,
    'Synthetic SQL Oracle remote project',
    'Local seed project requirement for sales email matching schema validation.',
    '["SQL", "Oracle", "Java"]'::jsonb,
    '["AWS"]'::jsonb,
    '{"db": ["SQL", "Oracle"], "language": ["Java"], "cloud": ["AWS"]}'::jsonb,
    700000,
    900000,
    'monthly_jpy',
    'Tokyo',
    'remote',
    '2026-07',
    '3 months',
    'SQL and Oracle engineer is required for a remote backend project.',
    'confirmed',
    '{"seed": true}'::jsonb
  FROM project_message
  RETURNING id
),
talent_row AS (
  INSERT INTO public.talent_profiles_from_email (
    message_id,
    anonymized_talent_key,
    summary,
    skills,
    skill_categories,
    experience_years,
    desired_rate_min,
    desired_rate_max,
    desired_location,
    remote_preference,
    availability_text,
    evidence_excerpt,
    review_status,
    metadata
  )
  SELECT
    id,
    'local_synthetic_talent_001',
    'Local seed talent profile for project-to-talent matching validation.',
    '["Java", "AWS", "API development"]'::jsonb,
    '{"language": ["Java"], "cloud": ["AWS"], "process": ["API development"]}'::jsonb,
    5,
    650000,
    850000,
    'Tokyo',
    'remote',
    '2026-07',
    'Java and AWS engineer is available from July.',
    'confirmed',
    '{"seed": true}'::jsonb
  FROM talent_message
  ON CONFLICT (anonymized_talent_key) DO UPDATE
  SET
    summary = EXCLUDED.summary,
    skills = EXCLUDED.skills,
    skill_categories = EXCLUDED.skill_categories,
    review_status = EXCLUDED.review_status,
    metadata = EXCLUDED.metadata
  RETURNING id
)
INSERT INTO public.requirement_skill_tags (
  project_requirement_id,
  talent_profile_id,
  skill_name,
  skill_category,
  importance,
  confidence,
  evidence_excerpt,
  metadata
)
SELECT id, NULL, 'SQL', 'db', 'required', 0.95, 'SQL and Oracle engineer is required.', '{"seed": true}'::jsonb
FROM project_row
UNION ALL
SELECT id, NULL, 'Oracle', 'db', 'required', 0.95, 'SQL and Oracle engineer is required.', '{"seed": true}'::jsonb
FROM project_row
UNION ALL
SELECT NULL, id, 'Java', 'language', 'experience', 0.9, 'Java and AWS engineer is available.', '{"seed": true}'::jsonb
FROM talent_row;
