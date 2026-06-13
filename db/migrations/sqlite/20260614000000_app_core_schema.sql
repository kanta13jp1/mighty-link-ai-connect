-- App core schema for local SQLite fallback.
-- Keep this aligned with src/app.py init_db until runtime initialization fully
-- moves to the migration runner.

CREATE TABLE IF NOT EXISTS engineers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    resume_raw TEXT,
    parsed_skills TEXT,
    career_goals TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(100),
    job_description TEXT,
    parsed_requirements TEXT,
    company_culture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engineer_id INTEGER,
    job_id INTEGER,
    fit_ratio REAL NOT NULL,
    score_skill INTEGER,
    score_culture INTEGER,
    score_growth INTEGER,
    score_performing INTEGER,
    match_summary TEXT,
    interview_questions TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(engineer_id) REFERENCES engineers(id) ON DELETE CASCADE,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
