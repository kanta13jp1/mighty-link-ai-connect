# 📐 Firebase / Supabase システムアーキテクチャ詳細設計書 (T730_1)

本ドキュメントは、エンジニア＆案件 AIフィットシミュレーター **『Mighty Skill-Bridge』** の本番インフラにおける、**Firebase**（Hosting / Auth / Cloud Functions）と **Supabase**（PostgreSQL / Row Level Security / Connection Pooling）のシステム連携アーキテクチャ詳細設計を定義します。

---

## 📅 バージョン履歴
| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-06 | v1.0.0 | 初版作成（システムアーキテクチャ設計・セキュリティ境界の定義） | Codex / AIエージェント |

---

## 1. 全体アーキテクチャ概要 (Architecture Overview)

本システムは、高いスケーラビリティ、運用保守コストの極小化、および強固なセキュリティ境界を両立するため、**サーバーレス（Firebase）** と **BaaS (Supabase)** を組み合わせたハイブリッド・アーキテクチャを採用します。

```mermaid
graph TD
    %% クライアント層
    subgraph Client [クライアント層 (ブラウザ)]
        FE[SPA フロントエンド / React or HTML5]
        AuthSDK[Firebase Auth SDK]
        DbSDK[Supabase Client SDK]
    end

    %% Firebase層
    subgraph FirebaseServices [Firebase (インフラ・コンポーネント)]
        Hosting[Firebase Hosting]
        Auth[Firebase Authentication]
        Functions[Firebase Cloud Functions / Python]
    end

    %% Supabase層
    subgraph SupabaseServices [Supabase (データ・セキュリティ)]
        Pool[PgBouncer / 接続プール]
        DB[(PostgreSQL Database)]
        RLS{Row Level Security}
    end

    %% 外部API層
    subgraph External [外部サービス]
        Gemini[Gemini API]
    end

    %% 接続関係
    FE -->|静的ファイル配信| Hosting
    FE -->|認証要求/IDトークン取得| AuthSDK
    AuthSDK -->|OAuth / Password| Auth
    
    %% API要求
    FE -->|API呼び出し / bearer Token| Functions
    Functions -->|IDトークン検証| Auth
    Functions -->|Gemini API コール| Gemini
    
    %% DB接続 (フロントエンドからの直接参照)
    FE -->|直接参照 / RLS適用| DbSDK
    DbSDK -->|JWT付きクエリ| RLS
    RLS -->|認可後クエリ実行| DB

    %% DB接続 (バックエンドからのサービス接続)
    Functions -->|Service Role Key / プール接続| Pool
    Pool -->|接続委譲| DB
```

---

## 2. コンポーネント定義と役割分担

### 2.1 Firebase 側コンポーネント

1. **Firebase Hosting**
   - **役割**: SPA (Single Page Application) のフロントエンド静的資産 (HTML / CSS / JS / 画像等) を高速グローバル CDN 経由で配信。
   - **本番移行の目的**: GitHub Pages での静的ホスティングから、認証情報やクローズド運用に適したカスタムドメイン・SSL証明書自動適用、および Firebase プロジェクトとのシームレスな統合への移行。
2. **Firebase Authentication**
   - **役割**: ユーザーのアカウント管理、サインイン (ID/Pass, Google OAuth 等)、セッションJWT（IDトークン）の生成・署名。
   - **重要性**: フロントエンドとバックエンド API の間の共通認証基盤として機能。
3. **Firebase Cloud Functions (Python 3.11+)**
   - **役割**: 重量級の計算（Gemini API を用いたエンジニア経歴書と案件情報のマルチモーダル解析・4軸スコアリングなど）を実行するバックエンド API の実行環境。
   - **理由**: 常時稼働による基本コストをゼロに抑えつつ、リクエスト数に応じたスケールアップが可能。

### 2.2 Supabase 側コンポーネント

1. **Supabase PostgreSQL**
   - **役割**: アプリケーションデータのプライマリデータストア（エンジニアプロファイル、案件候補ストック、利用規約同意履歴、AI監査ログ等）。
2. **Row Level Security (RLS)**
   - **役割**: データベーステーブルの行レベル認可ポリシー。フロントエンドから Supabase Client SDK で直接データをクエリする際、他人のデータへの不正アクセスを SQL レベルで遮断。
3. **PgBouncer (Connection Pooler)**
   - **役割**: Firebase Cloud Functions などのステートレス環境からの急激なデータベース同時接続の増加に対して、PostgreSQL の接続制限を超過しないようにプール管理。

---

## 3. 認証・セキュリティ設計 (Authentication & Security Boundaries)

本システムは、セキュアな2つのデータアクセス経路（**Direct-Access 経路** と **API-Proxy 経路**）を使い分けます。

### 3.1 Firebase Auth - Supabase DB 認証連携 (JWT検証)

Supabase PostgreSQL に適用される RLS は、クライアントが渡す JWT トークンに基づいて動作します。
1. フロントエンドは Firebase Auth SDK でサインインし、**Firebase IDトークン (JWT)** を取得します。
2. Supabase にアクセスする際、Firebase の JWT トークンを Supabase Client のヘッダーに設定、または Supabase の Auth 機能とカスタム JWT 署名鍵を共有し、Supabase 側で Firebase ユーザー ID (`sub`) を認識できるように設計します。
3. **代替案 (推奨簡素化構成)**: 
   - データの更新や機密クエリはすべて Firebase Cloud Functions (API-Proxy 経路) を通し、Functions 内で Firebase Admin SDK を用いて JWT を厳格にデコード・検証します。
   - 検証に合格したリクエストに限り、Functions から Supabase へ特権接続 (`service_role` キー) を用いてクエリを実行し、フロントエンドへ結果を返却します。これにより、Supabase 側の複雑な JWT 署名鍵連携コストを削減します。

### 3.2 SQL Row Level Security (RLS) ポリシー設計

データベーステーブルには、必ず以下の RLS ポリシーを適用し、API キーの流出時にもデータ漏洩を防ぎます。

```sql
-- テーブル: profiles (エンジニアプロファイル情報)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- ポリシー 1: 所有者本人のみ参照・更新可能 (auth.uid() は Firebase UID とマッピング)
CREATE POLICY "Users can view own profile" 
ON profiles FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" 
ON profiles FOR UPDATE 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- テーブル: audits (AI監査ログ)
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;

-- ポリシー 2: 管理者 (Service Role) のみがアクセス可能 (一般ユーザーの直接アクセスは一切不許可)
CREATE POLICY "Admins only access audits" 
ON audits TO service_role 
USING (true);
```

---

## 4. 接続プールおよびパフォーマンス最適化 (Connection Pooling)

サーバーレス環境（Firebase Functions）から Supabase PostgreSQL への接続数は、呼び出しスパイク時に急増し、DB側のプロセス上限に達するリスクがあります。

### 4.1 接続の物理的制限と対策
- **制限**: Supabase (PostgreSQL 15+) の最大直接接続数はインスタンスサイズによって制限（無料枠/スタータープランではおよそ 60 程度）。
- **対策**:
  1. **Supavisor トランザクションモード**: バックエンドから Supabase に接続する際、直接接続ではなく `pooler.supabase.com:6543`（Supavisor transaction mode）を使用します。T795 で本番 `SUPABASE_DB_URL` はこの形式へ切替済みです。
  2. **FastAPI / psycopg2 プーリングの最適化 (T759)**:
     - `SUPABASE_DB_POOL_MIN` = 1
     - `SUPABASE_DB_POOL_MAX` = 4（Functions/Cloud Run の各インスタンス内で小さく保つ）
     - `SUPABASE_DB_POOL_RECYCLE_SECONDS` = 1800
     - `SUPABASE_DB_POOL_PRE_PING` = True
     - `SUPABASE_DB_APPLICATION_NAME` = `mighty-skill-bridge-functions`
  3. `src/app.py` の `PooledPostgresConnection` は既存の `conn.close()` 呼び出しを pool 返却に変換し、呼び出しごとの物理接続作成を避けます。運用手順は [SUPABASE_CONNECTION_POOLING_RUNBOOK.md](SUPABASE_CONNECTION_POOLING_RUNBOOK.md) を正とします。

---

## 5. ローカル開発および統合テスト構成 (Local Development Workflow)

開発中の安全性を確保し、クラウド課金を防ぐため、ローカル開発時には両プロバイダのエミュレータ（ローカルスタック）を完全同期して稼働させます。
実行手順・検証項目・禁止事項は [LOCAL_DEV_EMULATOR_STACK_RUNBOOK.md](LOCAL_DEV_EMULATOR_STACK_RUNBOOK.md) を正とします。

```
[フロントエンド (localhost:3000)]
      │
      ├── (認証要求) ──> [Firebase Auth Emulator (localhost:9099)]
      │
      ├── (API要求)  ──> [Firebase Functions Emulator (localhost:5001)]
      │                        │
      │                  (DBクエリ/SQL)
      │                        ▼
      └────────────────> [Supabase Local PostgreSQL (localhost:54322 / CLI)]
```

### 5.1 Firebase Emulator Suite 設定 (`firebase.json`)
```json
{
  "emulators": {
    "auth": {
      "port": 9099
    },
    "functions": {
      "port": 5001
    },
    "hosting": {
      "port": 5000
    },
    "ui": {
      "enabled": true,
      "port": 4000
    },
    "singleProjectMode": true
  }
}
```

設定の静的検証は次で実行します。

```powershell
python scripts/verify_local_dev_stack.py --fail-on-critical
```

### 5.2 Supabase Local CLI 設定 (`supabase/config.toml`)
- ローカル PostgreSQL ポート: `54322`
- API ポート (GoTrue / REST): `54321`
- Studio ポート: `54323`
- seed は `supabase/seed.sql` の合成データのみを使用し、実メール・会社ドメインメール・production data は投入しない。
- スキーマ変更およびマイグレーションの履歴管理は、`supabase migration new` / `supabase db reset` と `scripts/manage_db_migrations.py` を併用し、手順は [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md) を正とする。

---

## 6. WBS 次フェーズへの接続

本アーキテクチャ詳細設計に基づき、後段のタスクを以下のように実装・実行します：
- **T730_2**: 本設計書のセキュリティポリシーを SQL 定義および Firebase rules へ落とし込む。
- **T731_1**: Supabase Database への migration SQL 実装および初期モックデータ投入。
- **T733_1/2**: Firebase Emulator と Supabase Local CLI を立ち上げ、テストスイートによる疎通確認を自動実行。
