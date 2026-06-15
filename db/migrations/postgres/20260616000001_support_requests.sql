-- Support request queue for user inquiries and escalation tracking.

CREATE TABLE IF NOT EXISTS support_requests (
    id SERIAL PRIMARY KEY,
    category VARCHAR(32) NOT NULL CHECK (category IN ('general', 'technical', 'billing', 'privacy', 'feedback')),
    priority VARCHAR(16) NOT NULL DEFAULT 'normal' CHECK (priority IN ('normal', 'high', 'urgent')),
    contact_email VARCHAR(254) NOT NULL,
    subject VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'triaged', 'in_progress', 'escalated', 'closed')),
    source VARCHAR(80) NOT NULL DEFAULT 'support_form',
    page_url TEXT,
    session_id VARCHAR(120),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_support_requests_status_priority
    ON support_requests(status, priority);

CREATE INDEX IF NOT EXISTS idx_support_requests_created_at
    ON support_requests(created_at);

ALTER TABLE support_requests ENABLE ROW LEVEL SECURITY;
