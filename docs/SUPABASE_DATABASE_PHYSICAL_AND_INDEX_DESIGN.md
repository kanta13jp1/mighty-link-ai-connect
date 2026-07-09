# 💾 Supabase Database 物理・インデックス設計書 (T730_3)

本ドキュメントは、**『Mighty Skill-Bridge』** のデータストアである Supabase PostgreSQL における、各エンティティのテーブル物理スキーマ定義（DDL）、インデックス設計、外部キー制約、整合性トリガー、およびデータライフサイクル運用方針を定義します。

---

## 📅 バージョン履歴
| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-06 | v1.0.0 | 初版作成（テーブル DDL、インデックス、トリガー定義） | Codex / AIエージェント |
| 2026-07-09 | v1.1.0 | 外部キー被覆 B-Tree インデックス設計（§2.3）を追加（T881）。全テーブル索引は `docs/database.md` §5 を正とする旨を明記 | Claude Code |

> 本書はコア診断ドメイン4テーブルの物理・インデックス設計を詳述する。フィードバック/サポート・営業メールAIマッチング（9表）・社内HR・アナリティクス/SLA を含む**全23テーブル+6ビューの索引は `supabase/migrations` を正本**とし、俯瞰は [`docs/database.md`](./database.md) §5 の全オブジェクト索引を参照。

---

## 1. 物理スキーマ定義 (Schema DDL)

データ整合性の維持、スケーラビリティ、および検索の高速化のため、PostgreSQL 15+ のネイティブ型（`UUID`, `JSONB`, `TIMESTAMP WITH TIME ZONE`）を活用した物理テーブル設計を行います。

### 1.1 タイムスタンプ自動更新トリガーの定義
すべてのテーブルで `updated_at` を自動的に更新するため、共通のトリガー関数を定義します。

```sql
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 1.2 物理テーブル DDL

#### 1.2.1 ユーザープロファイルテーブル (`profiles`)
- **役割**: エンジニアユーザーの基本プロファイルおよびマスキング済みレジュメ情報。

```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Firebase UID (インデックス必須)
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    resume_profile JSONB DEFAULT '{}'::jsonb, -- スキル・経験スタック
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TRIGGER set_timestamp_profiles
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
```

#### 1.2.2 案件フィットシミュレーション結果テーブル (`matches`)
- **役割**: AIによるエンジニアと案件票の突合・スコアリング結果履歴。

```sql
CREATE TABLE public.matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Firebase UID
    project_id VARCHAR(255) NOT NULL, -- 突合先案件ID
    fit_score NUMERIC(5, 2) NOT NULL, -- 総合フィットスコア (例: 85.50)
    score_details JSONB NOT NULL, -- 4軸評価の詳細スコア (structured_profile, gap_analysis等)
    matched_skills TEXT[] DEFAULT '{}'::text[], -- マッチしたスキルリスト
    missing_skills TEXT[] DEFAULT '{}'::text[], -- 不足しているスキルリスト
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_profile FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE
);

CREATE TRIGGER set_timestamp_matches
BEFORE UPDATE ON public.matches
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
```

#### 1.2.3 AI判定監査ログテーブル (`audits`)
- **役割**: AIの判定根拠、プロンプト履歴、生応答ログ。セキュリティ監査およびデバッグ用。

```sql
CREATE TABLE public.audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID, -- 該当シミュレーション結果ID
    prompt_version VARCHAR(50) NOT NULL, -- プロンプトテンプレートのバージョン
    raw_prompt TEXT NOT NULL, -- 送信プロンプト
    raw_response TEXT NOT NULL, -- 受信生のJSONレスポンス
    tokens_used INTEGER, -- 使用トークン数
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_match FOREIGN KEY (match_id) REFERENCES public.matches(id) ON DELETE SET NULL
);
```

#### 1.2.4 コスト・API制限メーターテーブル (`usage_ledgers`)
- **役割**: ユーザーごとのAPIコール数制限、当日利用トークン数、超過フラグの管理。

```sql
CREATE TABLE public.usage_ledgers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Firebase UID
    daily_calls_count INTEGER DEFAULT 0 NOT NULL, -- 本日の累積APIコール数
    daily_tokens_count INTEGER DEFAULT 0 NOT NULL, -- 本日の累積消費トークン数
    limit_exceeded BOOLEAN DEFAULT FALSE NOT NULL, -- コスト・利用数制限の超過フラグ
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL, -- 制限リセット予定時刻 (翌日AM0:00 JST)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT fk_profile_usage FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE
);

CREATE TRIGGER set_timestamp_usage_ledgers
BEFORE UPDATE ON public.usage_ledgers
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
```

---

## 2. インデックス設計 (Index Design)

クエリ実行計画を最適化し、本番でのスロークエリ（インデックス未使用スキャン）を防止するため、検索特性に応じたインデックスを構築します。

### 2.1 B-Tree インデックス（等価・範囲検索）

1. **`profiles (user_id)` / `usage_ledgers (user_id)`**:
   - 特徴: 単一の一意キー等価検索。
   - 設計: テーブル定義時に `UNIQUE` 制約を付与したことで、PostgreSQL によって自動的に一意 B-Tree インデックスが作成されます。
2. **`matches` の複合インデックス（`user_id`, `created_at`）**:
   - 特徴: フロントエンドで「特定のユーザーのシミュレーション履歴を最新順でリスト表示する」ユースケースに最適化。
   - 設計: 以下の複合インデックスを作成し、`ORDER BY created_at DESC` 時のファイルソートを回避します。
   ```sql
   CREATE INDEX idx_matches_user_created ON public.matches (user_id, created_at DESC);
   ```

### 2.2 GIN インデックス（JSONB検索）

1. **`profiles (resume_profile)` / `matches (score_details)`**:
   - 特徴: `JSONB` カラムの内部キーや配列型に対する部分一致・包含検索 (`?`, `@>`) を高速化。
   - 設計: GIN インデックスを構築し、インデックススキャンを可能にします。
   ```sql
   CREATE INDEX idx_profiles_resume_gin ON public.profiles USING gin (resume_profile);
   CREATE INDEX idx_matches_score_details_gin ON public.matches USING gin (score_details jsonb_path_ops);
   ```

### 2.3 外部キー被覆 B-Tree インデックス（T881）

PostgreSQL は PRIMARY KEY / UNIQUE 制約にのみ自動でインデックスを作成し、**外部キー列にはインデックスを張りません**。Supabase の Database Performance Advisor が「unindexed foreign keys」を検出する理由でもあり、未被覆のままだと (1) JOIN が逐次スキャンに退化し、(2) `ON DELETE CASCADE / SET NULL` の親行削除が全ての子テーブルを全走査します（データ保持・削除フロー T847 に直結）。

`supabase/migrations/20260709000000_fk_covering_indexes.sql` で、被覆が無かった外部キー列 11 件に単一列 B-Tree インデックスを追加しました（`CREATE INDEX IF NOT EXISTS`＝追加のみ・冪等）。

| テーブル | FK列 | 参照先 | 追加インデックス |
| :--- | :--- | :--- | :--- |
| `audits` | `match_id` | `matches(id)` | `idx_audits_match_id` |
| `sales_email_messages` | `mailbox_source_id` | `sales_mailbox_sources(id)` | `idx_sales_email_messages_mailbox_source_id` |
| `sales_email_messages` | `duplicate_of_id` | `sales_email_messages(id)` | `idx_sales_email_messages_duplicate_of_id` |
| `project_requirements` | `message_id` | `sales_email_messages(id)` | `idx_project_requirements_message_id` |
| `talent_profiles_from_email` | `message_id` | `sales_email_messages(id)` | `idx_talent_profiles_from_email_message_id` |
| `requirement_skill_tags` | `project_requirement_id` | `project_requirements(id)` | `idx_requirement_skill_tags_project_requirement_id` |
| `requirement_skill_tags` | `talent_profile_id` | `talent_profiles_from_email(id)` | `idx_requirement_skill_tags_talent_profile_id` |
| `email_parse_runs` | `mailbox_source_id` | `sales_mailbox_sources(id)` | `idx_email_parse_runs_mailbox_source_id` |
| `email_match_results` | `project_requirement_id` | `project_requirements(id)` | `idx_email_match_results_project_requirement_id` |
| `email_match_results` | `talent_profile_id` | `talent_profiles_from_email(id)` | `idx_email_match_results_talent_profile_id` |
| `email_match_feedback` | `match_result_id` | `email_match_results(id)` | `idx_email_match_feedback_match_result_id` |

> `sales_email_entities.message_id` は既存の複合インデックス `idx_sales_email_entities_message_type (message_id, entity_type)` の最左列で被覆済みのため追加不要。被覆の網羅は [`scripts/audit_fk_index_coverage.py`](../scripts/audit_fk_index_coverage.py)（10仮説・ギャップ0）と `tests/test_fk_index_coverage.py` が CI で継続検証する。大規模・高書き込みテーブルへ後日適用する場合は、トランザクション外の `CREATE INDEX CONCURRENTLY` を [`docs/PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md`](./PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md) の手順で用いる。**本番 Supabase への適用は運用者工程**（`SUPABASE_DB_URL` 必須、T778 の migration 適用バッチに合流可）。

---

## 3. データライフサイクルおよびローテーション設計 (Data Lifecycle & Maintenance)

監査ログ (`audits`) および利用メーター履歴は、時間の経過とともに劇的に肥大化し、ディスク容量の枯渇やインデックス再構成時のオーバーヘッドの原因となります。以下のクリーンアップ戦略を実装します。

### 3.1 監査ログ (`audits`) の保存ポリシー
- **保存期間**: 90日間。
- **アーカイブ**: 90日を経過した古いログは、本番データベースから論理ダンプして Google Cloud Storage (GCS) または Supabase Storage のコールドアーカイブバケットへ週次で転送し、本番データベースからは物理削除 (DELETE) を実行します。

### 3.2 コスト・メーター (`usage_ledgers`) の日次リセット
- **仕様**: 毎日午前0:00 (JST) に、すべてのユーザーの `daily_calls_count` および `daily_tokens_count` を `0` にリセットし、`limit_exceeded` を `FALSE` に戻します。
- **実行手段**: PostgreSQL pg_cron 拡張機能（Supabase のサポート機能）を利用したデータベース内定期ジョブ、もしくは Firebase Cloud Functions の Scheduled Trigger による日次自動バッチ。
