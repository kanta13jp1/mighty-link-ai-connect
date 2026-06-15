-- User feedback events for post-diagnosis helpfulness and NPS review.

CREATE TABLE IF NOT EXISTS feedback_events (
    id SERIAL PRIMARY KEY,
    match_result_id INTEGER REFERENCES match_results(id) ON DELETE SET NULL,
    rating VARCHAR(32) NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    nps_score INTEGER CHECK (nps_score BETWEEN 0 AND 10),
    comment TEXT,
    source VARCHAR(80) NOT NULL DEFAULT 'diagnosis_report',
    page_url TEXT,
    session_id VARCHAR(120),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_match_result_id ON feedback_events(match_result_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_created_at ON feedback_events(created_at);

ALTER TABLE feedback_events ENABLE ROW LEVEL SECURITY;
