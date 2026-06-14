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
