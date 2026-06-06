-- seed.sql
-- Mighty Skill-Bridge Initial Development Seeds

-- 1. Insert Dummy Profiles
INSERT INTO public.profiles (user_id, name, email, resume_profile)
VALUES (
    'user_9999',
    '梅澤 寛太',
    'k-umezawa@ml-mightylink.com',
    '{
        "title": "シニアAIフルスタックエンジニア",
        "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Google Cloud", "Firebase", "Supabase", "Docker", "Git"],
        "experience_years": 8,
        "recent_project": "AIエージェントによる自動コード生成および自律開発プラットフォームの開発"
    }'::jsonb
),
(
    'user_0001',
    'テスト 太郎',
    'taro.test@ml-mightylink.com',
    '{
        "title": "ジュニアフロントエンドエンジニア",
        "skills": ["HTML5", "CSS3", "JavaScript", "Vue.js", "Git"],
        "experience_years": 2,
        "recent_project": "社内業務ポータルサイトのフロントエンド実装"
    }'::jsonb
)
ON CONFLICT (user_id) DO NOTHING;

-- 2. Insert Dummy Matches (Simulation Results)
INSERT INTO public.matches (user_id, project_id, fit_score, score_details, matched_skills, missing_skills)
VALUES (
    'user_9999',
    'project_alpha_01',
    92.50,
    '{
        "technical_score": 95,
        "experience_score": 90,
        "fit_factor_4axis": {
            "skill_alignment": 95,
            "architecture_understanding": 90,
            "best_practices": 95,
            "security_compliance": 90
        },
        "gap_analysis": "技術的スタックは完全に一致。アーキテクチャ設計およびセキュリティ要件においてもシニアエンジニアとして十分な要件を満たしています。"
    }'::jsonb,
    ARRAY['Python', 'FastAPI', 'React', 'TypeScript', 'PostgreSQL', 'Firebase', 'Supabase'],
    ARRAY['Kubernetes']
),
(
    'user_9999',
    'project_beta_02',
    68.00,
    '{
        "technical_score": 70,
        "experience_score": 65,
        "fit_factor_4axis": {
            "skill_alignment": 70,
            "architecture_understanding": 60,
            "best_practices": 70,
            "security_compliance": 70
        },
        "gap_analysis": "Vue.js 開発案件であるのに対し、主に React 実績が中心であるため、技術的アライメントに多少のギャップあり。オンボーディング期間でのキャッチアップが必要です。"
    }'::jsonb,
    ARRAY['Python', 'PostgreSQL', 'Docker', 'Git'],
    ARRAY['Vue.js', 'Vuex']
),
(
    'user_0001',
    'project_beta_02',
    82.00,
    '{
        "technical_score": 85,
        "experience_score": 80,
        "fit_factor_4axis": {
            "skill_alignment": 85,
            "architecture_understanding": 80,
            "best_practices": 80,
            "security_compliance": 85
        },
        "gap_analysis": "ジュニアレベルの Vue.js 要件は満たしています。大規模設計やトランザクション処理に関してはサポートが必要です。"
    }'::jsonb,
    ARRAY['HTML5', 'CSS3', 'JavaScript', 'Vue.js', 'Git'],
    ARRAY[]::text[]
)
ON CONFLICT DO NOTHING;

-- 3. Insert Dummy Audits
INSERT INTO public.audits (match_id, prompt_version, raw_prompt, raw_response, tokens_used)
SELECT 
    id,
    'v1.0.0',
    'User Profile: [Python, FastAPI, React] \n Project details: [FastAPI developer role] \n Score technical alignment...',
    '{"fit_score": 92.5, "gap_analysis": "High alignment"}',
    1024
FROM public.matches
WHERE project_id = 'project_alpha_01'
LIMIT 1;

-- 4. Insert Dummy Usage Ledgers
INSERT INTO public.usage_ledgers (user_id, daily_calls_count, daily_tokens_count, limit_exceeded, reset_at)
VALUES (
    'user_9999',
    3,
    5200,
    FALSE,
    (timezone('utc'::text, now()) + interval '1 day') -- 明日の現在時刻
),
(
    'user_0001',
    0,
    0,
    FALSE,
    (timezone('utc'::text, now()) + interval '1 day')
)
ON CONFLICT (user_id) DO NOTHING;
