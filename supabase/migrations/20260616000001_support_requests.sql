-- Support requests captured through the API proxy.
-- RLS is enabled without anon policies so public REST access is denied.

CREATE TABLE IF NOT EXISTS public.support_requests (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL CHECK (category IN ('general', 'technical', 'billing', 'privacy', 'feedback')),
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('normal', 'high', 'urgent')),
    contact_email TEXT NOT NULL CHECK (char_length(contact_email) <= 254),
    subject TEXT NOT NULL CHECK (char_length(subject) BETWEEN 3 AND 160),
    message TEXT NOT NULL CHECK (char_length(message) BETWEEN 10 AND 3000),
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'triaged', 'in_progress', 'escalated', 'closed')),
    source TEXT NOT NULL DEFAULT 'support_form',
    page_url TEXT,
    session_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_support_requests_status_priority
    ON public.support_requests(status, priority);

CREATE INDEX IF NOT EXISTS idx_support_requests_created_at
    ON public.support_requests(created_at DESC);

CREATE TRIGGER set_timestamp_support_requests
BEFORE UPDATE ON public.support_requests
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

ALTER TABLE public.support_requests ENABLE ROW LEVEL SECURITY;
