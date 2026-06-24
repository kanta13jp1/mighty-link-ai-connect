-- Employee self-report responses captured through the API proxy (T840).
-- Direct identifiers are pseudonymized by FastAPI before insert.
-- RLS is enabled without anon policies so public REST access is denied.

CREATE TABLE IF NOT EXISTS public.employee_assessment_responses (
    id BIGSERIAL PRIMARY KEY,
    subject_pseudonym TEXT NOT NULL CHECK (char_length(subject_pseudonym) <= 120),
    department_bucket TEXT NOT NULL CHECK (char_length(department_bucket) BETWEEN 2 AND 80),
    motivation_level INTEGER NOT NULL CHECK (motivation_level BETWEEN 1 AND 5),
    culture_level INTEGER NOT NULL CHECK (culture_level BETWEEN 1 AND 5),
    growth_support_excerpt TEXT NOT NULL DEFAULT '' CHECK (char_length(growth_support_excerpt) <= 1000),
    consent_version TEXT NOT NULL CHECK (char_length(consent_version) <= 80),
    consented_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'reviewed', 'deleted')),
    source TEXT NOT NULL DEFAULT 'employee_assessment_form',
    page_url TEXT,
    session_id TEXT CHECK (session_id IS NULL OR char_length(session_id) <= 120),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    deletion_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_employee_assessment_subject
    ON public.employee_assessment_responses(subject_pseudonym);

CREATE INDEX IF NOT EXISTS idx_employee_assessment_created_at
    ON public.employee_assessment_responses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_employee_assessment_status
    ON public.employee_assessment_responses(status);

ALTER TABLE public.employee_assessment_responses ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.employee_assessment_responses FROM anon, authenticated;
