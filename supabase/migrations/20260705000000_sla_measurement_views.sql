-- T778: SLA measurement foundation (availability, response time, diagnosis accuracy).
-- uptime_checks stores samples recorded by scripts/check_uptime_targets.py --record-db.
-- Views are denied to anon/authenticated; the app and reporting scripts read them
-- through the pooled postgres connection only.
-- Note: the WAU view is matches-based because public.profiles has no last_login column
-- (docs/SLA_KPI_DEFINITION_AND_MEASUREMENT.md v1.0.0 draft assumed one).

CREATE TABLE IF NOT EXISTS public.uptime_checks (
    id BIGSERIAL PRIMARY KEY,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    target_id TEXT NOT NULL CHECK (char_length(target_id) <= 80),
    url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('UP', 'WARNING', 'DOWN')),
    http_status INTEGER,
    response_ms INTEGER CHECK (response_ms IS NULL OR response_ms >= 0),
    source TEXT NOT NULL DEFAULT 'check_uptime_targets',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_uptime_checks_checked_at
    ON public.uptime_checks(checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_uptime_checks_target
    ON public.uptime_checks(target_id, checked_at DESC);

ALTER TABLE public.uptime_checks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.uptime_checks FROM anon, authenticated;
REVOKE ALL ON SEQUENCE public.uptime_checks_id_seq FROM anon, authenticated;

-- 3.1 daily diagnoses (business KPI)
CREATE OR REPLACE VIEW public.kpi_daily_diagnoses AS
SELECT
    DATE_TRUNC('day', created_at AT TIME ZONE 'Asia/Tokyo') AS diagnosis_date,
    COUNT(*) AS diagnosis_count,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(fit_score) AS avg_fit_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fit_score) AS median_fit_score
FROM public.matches
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1 DESC;

-- 3.2 weekly active users (matches-based: active = ran a diagnosis)
CREATE OR REPLACE VIEW public.kpi_weekly_active_users AS
SELECT
    DATE_TRUNC('week', created_at AT TIME ZONE 'Asia/Tokyo') AS week_start,
    COUNT(DISTINCT user_id) AS wau
FROM public.matches
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1 DESC;

-- 3.2b weekly anonymous demo sessions (T800 analytics)
CREATE OR REPLACE VIEW public.kpi_weekly_anonymous_sessions AS
SELECT
    DATE_TRUNC('week', created_at AT TIME ZONE 'Asia/Tokyo') AS week_start,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_pseudonym) AS anonymous_sessions
FROM public.usage_analytics_events
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1 DESC;

-- 3.3 monthly availability (SLA: pilot 99.5%)
CREATE OR REPLACE VIEW public.kpi_monthly_availability AS
SELECT
    DATE_TRUNC('month', checked_at AT TIME ZONE 'Asia/Tokyo') AS month,
    target_id,
    COUNT(*) AS total_checks,
    SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS up_checks,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) / COUNT(*),
        3
    ) AS availability_pct
FROM public.uptime_checks
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- 3.4 daily response time percentiles (SLA: P95 <= 3000ms)
CREATE OR REPLACE VIEW public.kpi_daily_response_time AS
SELECT
    DATE_TRUNC('day', checked_at AT TIME ZONE 'Asia/Tokyo') AS check_date,
    target_id,
    COUNT(*) AS samples,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_ms))::numeric, 1) AS p50_ms,
    ROUND((PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_ms))::numeric, 1) AS p95_ms,
    MAX(response_ms) AS max_ms
FROM public.uptime_checks
WHERE response_ms IS NOT NULL
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- 3.5 weekly diagnosis accuracy (KPI: helpful rate >= 70%)
CREATE OR REPLACE VIEW public.kpi_weekly_diagnosis_accuracy AS
SELECT
    DATE_TRUNC('week', created_at AT TIME ZONE 'Asia/Tokyo') AS week_start,
    COUNT(*) FILTER (WHERE rating = 'helpful') AS helpful_count,
    COUNT(*) FILTER (WHERE rating = 'not_helpful') AS not_helpful_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE rating = 'helpful')
        / NULLIF(COUNT(*) FILTER (WHERE rating IN ('helpful', 'not_helpful')), 0),
        1
    ) AS helpful_pct
FROM public.feedback_events
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1 DESC;

REVOKE ALL ON public.kpi_daily_diagnoses FROM anon, authenticated;
REVOKE ALL ON public.kpi_weekly_active_users FROM anon, authenticated;
REVOKE ALL ON public.kpi_weekly_anonymous_sessions FROM anon, authenticated;
REVOKE ALL ON public.kpi_monthly_availability FROM anon, authenticated;
REVOKE ALL ON public.kpi_daily_response_time FROM anon, authenticated;
REVOKE ALL ON public.kpi_weekly_diagnosis_accuracy FROM anon, authenticated;
