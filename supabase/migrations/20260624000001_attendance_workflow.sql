-- Attendance punch and timesheet approval workflow (T841).
-- Direct identifiers and raw files are pseudonymized or discarded by FastAPI before insert.
-- RLS is enabled without anon policies so public REST access is denied.

CREATE TABLE IF NOT EXISTS public.attendance_punch_events (
    id BIGSERIAL PRIMARY KEY,
    subject_pseudonym TEXT NOT NULL CHECK (char_length(subject_pseudonym) <= 120),
    event_type TEXT NOT NULL CHECK (event_type IN ('clock_in', 'clock_out', 'break_start', 'break_end')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL DEFAULT 'attendance_widget',
    page_url TEXT,
    session_id TEXT CHECK (session_id IS NULL OR char_length(session_id) <= 120),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.attendance_timesheet_imports (
    id BIGSERIAL PRIMARY KEY,
    subject_pseudonym TEXT NOT NULL CHECK (char_length(subject_pseudonym) <= 120),
    file_digest TEXT NOT NULL CHECK (char_length(file_digest) <= 80),
    file_extension TEXT NOT NULL CHECK (char_length(file_extension) <= 16),
    work_minutes INTEGER NOT NULL DEFAULT 0 CHECK (work_minutes >= 0),
    overtime_minutes INTEGER NOT NULL DEFAULT 0 CHECK (overtime_minutes >= 0),
    holiday_work_days INTEGER NOT NULL DEFAULT 0 CHECK (holiday_work_days >= 0),
    midnight_minutes INTEGER NOT NULL DEFAULT 0 CHECK (midnight_minutes >= 0),
    anomaly_count INTEGER NOT NULL DEFAULT 0 CHECK (anomaly_count >= 0),
    status TEXT NOT NULL DEFAULT 'pending_approval' CHECK (status IN ('pending_approval', 'approved', 'rejected', 'manual_review')),
    consent_version TEXT NOT NULL CHECK (char_length(consent_version) <= 80),
    source TEXT NOT NULL DEFAULT 'attendance_timesheet_upload',
    page_url TEXT,
    session_id TEXT CHECK (session_id IS NULL OR char_length(session_id) <= 120),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attendance_punch_subject
    ON public.attendance_punch_events(subject_pseudonym);

CREATE INDEX IF NOT EXISTS idx_attendance_punch_recorded_at
    ON public.attendance_punch_events(recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_attendance_timesheet_subject
    ON public.attendance_timesheet_imports(subject_pseudonym);

CREATE INDEX IF NOT EXISTS idx_attendance_timesheet_status
    ON public.attendance_timesheet_imports(status);

CREATE INDEX IF NOT EXISTS idx_attendance_timesheet_created_at
    ON public.attendance_timesheet_imports(created_at DESC);

ALTER TABLE public.attendance_punch_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_timesheet_imports ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.attendance_punch_events FROM anon, authenticated;
REVOKE ALL ON TABLE public.attendance_timesheet_imports FROM anon, authenticated;
