-- 20260606000000_init_schema.sql
-- Supabase PostgreSQL Initial Migration

-- 1. Helper function to extract Firebase User ID from request JWT
CREATE OR REPLACE FUNCTION auth.firebase_uid()
RETURNS text AS $$
  SELECT 
    coalesce(
      nullif(current_setting('request.jwt.claim.sub', true), ''),
      nullif(current_setting('request.jwt.claims', true)::jsonb->>'sub', '')
    )::text;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- 2. Helper function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Profiles Table
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    resume_profile JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TRIGGER set_timestamp_profiles
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- 4. Matches Table
CREATE TABLE public.matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    fit_score NUMERIC(5, 2) NOT NULL,
    score_details JSONB NOT NULL,
    matched_skills TEXT[] DEFAULT '{}'::text[],
    missing_skills TEXT[] DEFAULT '{}'::text[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_profile FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE
);

CREATE TRIGGER set_timestamp_matches
BEFORE UPDATE ON public.matches
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- 5. Audits Table
CREATE TABLE public.audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID,
    prompt_version VARCHAR(50) NOT NULL,
    raw_prompt TEXT NOT NULL,
    raw_response TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_match FOREIGN KEY (match_id) REFERENCES public.matches(id) ON DELETE SET NULL
);

-- 6. Usage Ledgers Table
CREATE TABLE public.usage_ledgers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE,
    daily_calls_count INTEGER DEFAULT 0 NOT NULL,
    daily_tokens_count INTEGER DEFAULT 0 NOT NULL,
    limit_exceeded BOOLEAN DEFAULT FALSE NOT NULL,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_profile_usage FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE
);

CREATE TRIGGER set_timestamp_usage_ledgers
BEFORE UPDATE ON public.usage_ledgers
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- 7. Indexes Design
CREATE INDEX idx_matches_user_created ON public.matches (user_id, created_at DESC);
CREATE INDEX idx_profiles_resume_gin ON public.profiles USING gin (resume_profile);
CREATE INDEX idx_matches_score_details_gin ON public.matches USING gin (score_details jsonb_path_ops);

-- 8. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_ledgers ENABLE ROW LEVEL SECURITY;

-- 9. Row Level Security Policies
-- Profiles
CREATE POLICY "Allow individual read own profile" 
ON public.profiles FOR SELECT 
USING (auth.firebase_uid() = user_id);

CREATE POLICY "Allow individual update own profile" 
ON public.profiles FOR UPDATE 
USING (auth.firebase_uid() = user_id) 
WITH CHECK (auth.firebase_uid() = user_id);

CREATE POLICY "Allow individual insert own profile" 
ON public.profiles FOR INSERT 
WITH CHECK (auth.firebase_uid() = user_id);

-- Matches
CREATE POLICY "Allow individual read own matches" 
ON public.matches FOR SELECT 
USING (auth.firebase_uid() = user_id);

CREATE POLICY "Allow individual insert own matches" 
ON public.matches FOR INSERT 
WITH CHECK (auth.firebase_uid() = user_id);

CREATE POLICY "Allow individual delete own matches" 
ON public.matches FOR DELETE 
USING (auth.firebase_uid() = user_id);

-- Usage Ledgers
CREATE POLICY "Allow individual read own usage ledger" 
ON public.usage_ledgers FOR SELECT 
USING (auth.firebase_uid() = user_id);
