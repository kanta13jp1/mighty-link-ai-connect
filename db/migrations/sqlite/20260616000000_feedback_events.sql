-- User feedback events for local SQLite fallback.

CREATE TABLE IF NOT EXISTS feedback_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_result_id INTEGER,
    rating VARCHAR(32) NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    nps_score INTEGER CHECK (nps_score IS NULL OR (nps_score BETWEEN 0 AND 10)),
    comment TEXT,
    source VARCHAR(80) NOT NULL DEFAULT 'diagnosis_report',
    page_url TEXT,
    session_id VARCHAR(120),
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(match_result_id) REFERENCES match_results(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_match_result_id ON feedback_events(match_result_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_created_at ON feedback_events(created_at);
