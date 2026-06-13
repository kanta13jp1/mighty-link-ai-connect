-- App core schema for Supabase/PostgreSQL runtime tables.
-- Supabase product-domain tables remain in supabase/migrations.

CREATE TABLE IF NOT EXISTS engineers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    resume_raw TEXT,
    parsed_skills TEXT,
    career_goals TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(100),
    job_description TEXT,
    parsed_requirements TEXT,
    company_culture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS match_results (
    id SERIAL PRIMARY KEY,
    engineer_id INTEGER REFERENCES engineers(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    fit_ratio REAL NOT NULL,
    score_skill INTEGER,
    score_culture INTEGER,
    score_growth INTEGER,
    score_performing INTEGER,
    match_summary TEXT,
    interview_questions TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE engineers ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_results ENABLE ROW LEVEL SECURITY;
