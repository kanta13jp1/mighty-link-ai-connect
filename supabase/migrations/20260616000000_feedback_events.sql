-- User feedback events captured through the API proxy.
-- RLS is enabled without anon policies so public REST access is denied.

CREATE TABLE IF NOT EXISTS public.feedback_events (
    id BIGSERIAL PRIMARY KEY,
    match_result_id INTEGER,
    rating TEXT NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    nps_score INTEGER CHECK (nps_score BETWEEN 0 AND 10),
    comment TEXT CHECK (char_length(comment) <= 1000),
    source TEXT NOT NULL DEFAULT 'diagnosis_report',
    page_url TEXT,
    session_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_match_result_id
    ON public.feedback_events(match_result_id);

CREATE INDEX IF NOT EXISTS idx_feedback_events_created_at
    ON public.feedback_events(created_at DESC);

ALTER TABLE public.feedback_events ENABLE ROW LEVEL SECURITY;
