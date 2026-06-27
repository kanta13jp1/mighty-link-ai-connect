-- T800: privacy-preserving product usage analytics event ledger.
-- This table stores only pseudonymized session IDs, coarse browser family,
-- route-level page paths, and sanitized metadata. It intentionally excludes
-- IP addresses, raw User-Agent strings, names, emails, and form contents.

CREATE TABLE IF NOT EXISTS public.usage_analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_name TEXT NOT NULL
        CHECK (event_name IN ('page_view', 'section_view', 'cta_click', 'form_submit', 'form_success', 'form_error', 'dashboard_export')),
    event_surface TEXT NOT NULL DEFAULT 'public_demo'
        CHECK (event_surface IN ('public_demo', 'firebase_app', 'internal_console')),
    page_path TEXT,
    session_pseudonym TEXT NOT NULL,
    user_agent_family TEXT NOT NULL DEFAULT 'unknown',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_events_event_name
    ON public.usage_analytics_events(event_name);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_events_created_at
    ON public.usage_analytics_events(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_events_session
    ON public.usage_analytics_events(session_pseudonym);

ALTER TABLE public.usage_analytics_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.usage_analytics_events FROM anon, authenticated;
REVOKE ALL ON SEQUENCE public.usage_analytics_events_id_seq FROM anon, authenticated;
