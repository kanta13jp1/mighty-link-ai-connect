# 🔒 Firebase Auth & Supabase RLS セキュリティ設計書 (T730_2)

本ドキュメントは、**『Mighty Skill-Bridge』** において、Firebase Authentication によるユーザー認証と、Supabase PostgreSQL の Row Level Security (RLS) によるデータ認可を安全に連携させ、強固なアクセス制御（ゼロトラスト・データアクセス）を実装するための詳細セキュリティ設計仕様を定義します。

---

## 📅 バージョン履歴
| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-06 | v1.0.0 | 初版作成（Firebase JWT連携、RLSポリシー定義、特権境界の定義） | Codex / AIエージェント |

---

## 1. 認証とセキュリティの基本設計方針

本システムのデータ保護モデルは、「最小特権の原則（Least Privilege Principle）」に基づき、データストアへのアクセス経路を厳格に制御します。

1. **アクセス制限の二重防御（Defense-in-Depth）**
   - **第一層 (APIエンドポイント認証)**: バックエンド API (Firebase Cloud Functions) の呼び出し時に Firebase ID トークンを必須とし、正当な認証済みユーザーのみが処理を実行可能にします。
   - **第二層 (データベース認可 / RLS)**: Supabase PostgreSQL 側で RLS ポリシーを有効化し、万が一クライアントの API キーや JWT トークンが漏洩、もしくはバックエンド API に脆弱性があっても、データベースレベルで他人のデータへの不正操作を防御します。
2. **クライアントキーの隔離**
   - クライアント（フロントエンド）に配布する API キーは、常に制限付きの **`anon` キー** (Public API Key) のみとします。
   - データベースの全操作権限を持つ **`service_role` キー** (Admin API Key) は、絶対にクライアントに露出させず、Firebase Cloud Functions の環境変数（シークレットマネージャー）内のみに隔離します。

---

## 2. Firebase Auth - Supabase 認証連携 (JWTカスタムクレーム連携)

フロントエンドから Supabase への直接アクセスを可能にし、かつ所有者本人に限定する RLS を機能させるため、以下の JWT 連携を行います。

### 2.1 Firebase ID トークン（JWT）の検証フロー

Supabase は、外部で署名されたカスタム JWT を検証する仕組み、もしくはデータベース関数を用いて Firebase トークンを解析する仕組みを提供します。

```
[フロントエンド]
      │
   1. 認証要求 ──> [Firebase Auth]
      │
   2. Firebase IDトークン(JWT) 返却
      │
      ├── 3a. (Direct-Access経路) ──> [Supabase Rest API (RLS適用)]
      │         ユーザーIDを JWT クレームの `sub` (Firebase UID) から抽出し検証
      │
      └── 3b. (API-Proxy経路) ─────> [Firebase Functions] ──> [Supabase (Service Role)]
                IDトークンを検証し、内部関数で特権クエリを実行
```

### 2.2 PostgreSQL ヘルパー関数の作成

データベース層で Firebase Auth 由来の認証トークンからユーザー UID を安全に取得するため、以下の PostgreSQL ヘルパー関数を作成し、各 RLS ポリシーで利用します。

```sql
-- 関数: public.firebase_uid()
-- クライアントから渡された JWT トークンのクレームから、Firebase のユーザーUID (sub) を抽出する
CREATE OR REPLACE FUNCTION public.firebase_uid()
RETURNS text AS $$
  SELECT 
    coalesce(
      nullif(current_setting('request.jwt.claim.sub', true), ''),
      nullif(current_setting('request.jwt.claims', true)::jsonb->>'sub', '')
    )::text;
$$ LANGUAGE sql STABLE SECURITY DEFINER;
```

---

## 3. テーブルごとの Row Level Security (RLS) ポリシー設計

各データベーステーブルに適用する、具体的な SQL 構文による RLS ポリシー定義です。

### 3.1 ユーザープロファイルテーブル (`profiles`)
- **ポリシー方針**: 所有者本人のみが参照・更新でき、他人のプロファイルは一切参照不可。管理者は全参照可能。

```sql
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 自身のプロファイルの参照を許可
CREATE POLICY "Allow individual read own profile" 
ON public.profiles FOR SELECT 
USING (public.firebase_uid() = user_id);

-- 自身のプロファイルの更新を許可
CREATE POLICY "Allow individual update own profile" 
ON public.profiles FOR UPDATE 
USING (public.firebase_uid() = user_id) 
WITH CHECK (public.firebase_uid() = user_id);

-- 自身のプロファイルの作成を許可
CREATE POLICY "Allow individual insert own profile" 
ON public.profiles FOR INSERT 
WITH CHECK (public.firebase_uid() = user_id);
```

### 3.2 案件シミュレーション結果テーブル (`matches`)
- **ポリシー方針**: 本人のみ参照、追加、更新可能。

```sql
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;

-- 自身のシミュレーション結果の参照
CREATE POLICY "Allow individual read own matches" 
ON public.matches FOR SELECT 
USING (public.firebase_uid() = user_id);

-- 自身のシミュレーション結果の追加
CREATE POLICY "Allow individual insert own matches" 
ON public.matches FOR INSERT 
WITH CHECK (public.firebase_uid() = user_id);

-- 自身のシミュレーション結果の削除 (論理削除は UPDATE なので、ここでは物理削除)
CREATE POLICY "Allow individual delete own matches" 
ON public.matches FOR DELETE 
USING (public.firebase_uid() = user_id);
```

### 3.3 AI判定監査ログテーブル (`audits`)
- **ポリシー方針**: 一般ユーザーは一切参照・更新・作成不可。バックエンド API (サービスロールキー) からのみ読み書き可能。

```sql
ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;

-- service_role キーからのみアクセス可能にするため、一般ユーザー向けのポリシーはすべて未定義（デフォルトでアクセス禁止）
-- データベースに対する service_role 接続は、デフォルトで RLS をバイパスするためポリシーの記述は不要
```

### 3.4 API利用制限メーター・コスト台帳テーブル (`usage_ledgers`)
- **ポリシー方針**: 本人は現在の利用残高・コール数の参照のみ可能。値の更新（インクリメントなど）は、バックエンド API (サービスロールキー) による特権処理でのみ実行可能（一般ユーザーによる自己改ざんの防止）。

```sql
ALTER TABLE public.usage_ledgers ENABLE ROW LEVEL SECURITY;

-- 自身の利用メーターの参照のみ許可
CREATE POLICY "Allow individual read own usage ledger" 
ON public.usage_ledgers FOR SELECT 
USING (public.firebase_uid() = user_id);

-- INSERT / UPDATE / DELETE ポリシーは一般ユーザー向けには定義しない（service_role のみ許可）
```

---

## 4. 特権 API 接続の境界設計 (API Privilege Separation)

一般ユーザー権限でのデータベース操作と、バックエンド API による特権操作は、接続時に使用する「ロール（Role）」によって物理的・論理的に分離します。

```
[一般クエリ]   ──(anon キー)─────────> [PostgreSQL / authenticated ロール] ──> (RLS適用)
[特権API操作]  ──(service_role キー)─> [PostgreSQL / service_role ロール]   ──> (RLSをバイパス)
```

1. **`authenticated` ロールによる接続**
   - フロントエンドから直接 REST API や GraphQL を介して Supabase にアクセスする際、クライアントの Firebase IDトークンに基づき、PostgreSQL 上の `authenticated` ロールとして実行されます。
   - このロールには RLS ポリシーが 100% 適用されます。
2. **`service_role` ロールによる接続**
   - バックエンド API が Gemini API スコア記録や audits 監査ログの書き込みを行う際は、`supabase-py` Client に `service_role` キーを設定して接続します。
   - このロールは PostgreSQL 上でスーパーユーザー扱いに近く、RLS ポリシーを強制バイパスしてクエリを実行できるため、不正防止のためキーの安全性を厳格に管理します。

---

## 5. ローカルテストおよびポリシー検証計画 (Testing & Verification)

本セキュリティポリシーが正しく動作すること（認可の妥当性、および不正アクセス時の拒否）を、Supabase CLI エミュレータを用いてテストします。

### 5.1 ユニットテストコード（SQL / pgTAP 構成例）

`supabase/tests/database/rls_test.sql` を配置し、ローカルで RLS 検証テストを実行可能な状態にします。

```sql
-- pgTAP を用いたセキュリティテスト
BEGIN;
SELECT plan(4);

-- テストユーザーのモック設定 (Firebase UID = 'user_9999')
SELECT tests.authenticate_as('user_9999');

-- テスト 1: 自身のプロファイルを作成できること
INSERT INTO public.profiles (user_id, name) VALUES ('user_9999', 'Test User')
RETURNING id;
SELECT is( (SELECT name FROM public.profiles WHERE user_id = 'user_9999'), 'Test User', 'Should insert own profile' );

-- テスト 2: 他人のプロファイルを挿入しようとすると失敗すること
SELECT throws_ok(
  $$ INSERT INTO public.profiles (user_id, name) VALUES ('user_other', 'Stolen Identity') $$,
  'new row violates row-level security policy for table "profiles"',
  'Should prevent inserting other users profile'
);

-- テスト 3: 他人のプロファイルをクエリしても何も返らないこと
SELECT is_empty(
  $$ SELECT * FROM public.profiles WHERE user_id = 'user_other' $$,
  'Should not be able to read others profile'
);

-- テスト 4: audits テーブルに直接アクセスしようとすると失敗すること
SELECT throws_ok(
  $$ SELECT * FROM public.audits $$,
  'permission denied for table audits',
  'Should prevent public access to audits table'
);

SELECT * FROM finish();
ROLLBACK;
```
