# 🌐 Mighty Skill-Bridge: ホスティング先およびデータベースインフラ最終選定報告書 (HOSTING_AND_DATABASE_SELECTION.md)

> **Mighty-Link AI Connect: Project "Mighty Skill-Bridge"**
> *社長意思決定（Firebase & Supabase 構成）に基づき、信頼性・セキュリティ・費用対効果を最大化するプロダクションインフラ報告書*

---

## 1. はじめに

本報告書は、WBSタスク **T730** の調査結果および**社長の最終意思決定（ホスティング：Firebase、データベース：Supabase）**に基づき、エンジニアと案件の多次元AIフィットシミュレーター『Mighty Skill-Bridge』の本番プロダクション稼働に向けたインフラアーキテクチャ設計を確定したものです。

Firebase と Supabase というモダンかつ超強力なバックエンド・アズ・ア・サービス (BaaS/PaaS) の組み合わせにより、**初期固定費 $0 (完全無料)** からスタートでき、1日1時間の稼働でも極めて安全・迅速にCI/CDデプロイが可能な「ゼロOps」アーキテクチャを実現します。

---

## 2. ホスティング先：Firebase (Firebase Hosting & Cloud Functions)

FastAPI (Python) バックエンドと静的フロントエンド (index.html) の配信プラットフォームとして、Googleの **Firebase** を採用します。

### アーキテクチャとメリット：
1. **Firebase Hosting (フロントエンド配信)**:
   * **超高速配信**: グローバルCDNにより、クライアント側のSPA/HTMLをミリ秒単位で爆速配信します。
   * **SSL/TLS自動付与**: Let's EncryptによるTLS証明書の自動更新・適用が完全無料で提供されます。
   * **プレビューチャンネル**: PR（プルリクエスト）ごとに一時的な検証用URLを自動発行でき、本番マージ前の社長確認が容易になります。
2. **Firebase Cloud Functions (FastAPI バックエンド)**:
   * **サーバーレス実行**: FastAPIアプリケーションを `mangum` などのASGIアダプターでラップし、サーバーレスコンテナとして動かします。アクセスがない時は自動でスリープし、アクセス時にミリ秒で起動するため、余計なリソース代が一切発生しません。
   * **GitHub Actions連携**: `firebase-tools` CLIおよびGitHub Actionsを利用し、`main`/`master` マージ時に1コマンドで全自動デプロイが完了します。

---

## 3. データベース：Supabase (マネージド PostgreSQL)

データ保持、および多次元AIフィット結果（`match_results`）を堅牢に格納するため、オープンソースの Firebase 代替であり極めて強力な **Supabase** を採用します。

### アーキテクチャとメリット：
1. **マネージド PostgreSQL データベース**:
   * SQLite3と比較して、完全なトランザクション整合性、高度なスキーマ制約、強力なクエリ性能を標準装備。将来のマルチユーザー/同時書き込みでも競合が発生しません。
2. **REST API & セキュリティ (Row Level Security)**:
   * データベースを作成するだけで、セキュアなREST APIが自動生成されます。また、行レベルセキュリティ (RLS) を用いて、特定ユーザーのデータのみアクセス可能にする強固な認可制御が標準で備わっています。
3. **無料枠 (Free Tier) の適用**:
   * 500MBのデータベース容量、および週次自動バックアップ、月5万の認証ユーザー数が**完全無料 ($0.00 / 月)** で提供されており、パイロット運用には十分すぎるスペックです。

---

## 4. プロダクション環境の最終システム構成図

社長意思決定に基づき、Mighty Skill-Bridgeのプロダクションローンチにおけるインフラ構成を以下のように確定します。

```mermaid
graph TD
    User([パイロット利用者/寛太]) -->|Basic Auth| FB_Host[Firebase Hosting]
    FB_Host -->|API Route /api/*| FB_Func[Firebase Cloud Functions / FastAPI]
    FB_Func -->|PostgreSQL接続| Supabase[(Supabase / Managed PostgreSQL)]
    FB_Func -->|Auto Sync| Sheets[(Google Sheets WBS/課題管理表/マッチログ)]
    FB_Func -->|Timer Trigger| Calendar[(Google Calendar 開発計画)]
    
    subgraph Firebase (Google Cloud)
        FB_Host
        FB_Func
    end
    
    subgraph Database Layer
        Supabase
    end
    
    subgraph Google Workspace API
        Sheets
        Calendar
    end
```

### 月額ランニングコスト見積もり (Firebase & Supabase 構成)

| コンポーネント | サービス名 / 仕様 | 月額費用 | 備考 |
| :--- | :--- | :--- | :--- |
| **ホスティング (静的)** | Firebase Hosting (Sparkプラン) | **$0.00 (完全無料)** | グローバルCDN、SSL自動付与 |
| **バックエンド (API)** | Firebase Cloud Functions (Pay-as-you-go) | **$0.00** | 無料枠範囲内 (月200万呼び出しまで無料) |
| **データベース** | Supabase PostgreSQL (Free Tier) | **$0.00 (完全無料)** | 500MB容量、自動インデックス、REST API付 |
| **ドメイン & SSL** | ml-mightylink.com (カスタム統合) | 既存のドメインを活用 | Firebase HostingがSSL証明書を無料管理 |
| **Google Workspace** | Calendar, Sheets, Drive API | 既存アカウント範囲内 | $0.00 (追加費用なし) |
| **合計固定費** | — | **$0.00 (完全無料)** | **初期投資リスクゼロで、世界最高峰のインフラを入手可能** |

---

## 5. 次のアクション（Firebase ＆ Supabase のプロビジョニング）

社長のFirebase & Supabase方針に基づき、以下のセキュリティ＆シークレット管理（**T732**）およびバックエンド実装（**T731**）を調整・実施します。

1. **[T732] Firebase/Supabase シークレット管理と環境変数定義**:
   * Firebase Cloud Functions の環境変数設定（Firebase Functions Config または Google Cloud Secret Manager）に `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GOOGLE_CREDENTIALS_JSON` などの環境変数を安全に登録します。
2. **[T731] バックエンド接続 PoC (SQLAlchemy / Supabase Python Client)**:
   * FastAPI内から PostgreSQL (Supabase) に接続するための `SQLAlchemy` または `asyncpg` 設定を `src/app.py` に組み込み、ローカルSQLite/InMemoryとシームレスに切り替え可能なマルチDBドライバー設計を実装します。

---
*Approved and finalized by the CEO. Document updated under WBS Task T730 / T732.*
