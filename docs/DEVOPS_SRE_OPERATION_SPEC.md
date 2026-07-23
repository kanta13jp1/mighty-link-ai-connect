# DevOps / SRE 運用仕様書 & アーキテクチャ決定（T896, T870, T778, コスト, ログ, パフォーマンス）

作成日: 2026-07-23  
更新日: 2026-07-23 (深掘り運用規定追加)  
担当責任者: **DevOps / SRE スペシャリスト（鈴木 一郎）**  
対象領域: クラウドインフラ（Firebase/GCP/Supabase）、GitHub Actions CI/CD、DBバックアップ、SLA/DR、コスト管理、セキュリティ鍵運用、DBパフォーマンス

---

## 1. 概要 & 基本方針

本ドキュメントは、Mighty Link AI Connect プロジェクトにおける DevOps / SRE 領域の基本方針、CI/CD デプロイ制御、DBバックアップ・災害復旧（DR）運用、SLA/稼働モニタリング設計、クラウドコスト管理、ログ・Secretローテーション、および DB パフォーマンス診断を定めた包括的運用仕様書です。

---

## 2. インフラ & CI/CD デプロイ制御方針（T896）

### 2.1 デプロイパイプライン設計 (`.github/workflows/deploy.yml`)
- **トリガー条件**: `main` ブランチへのプッシュ・マージ、および `workflow_dispatch`（手動実行）。
- **コミット検出ロジック**: `fetch-depth: 0` を設定し、複数コミット一括 push 時の取りこぼしを完全に防ぐ。
- **デプロイ対象**:
  - **Firebase Hosting**: 本番アプリ基盤 (`mightylink-app.com`)
  - **GitHub Pages**: 社長報告・受入テスト用公開デモ (`https://kanta13jp1.github.io/mighty-link-ai-connect/`)

### 2.2 本番リリース制御 & ロールバック戦略
1. **リリース前提条件**: `main` ブランチへのマージ前に、フルプリフライト・ガード (`python scripts/run_lane_preflight.py --full`) の全件 PASS を必須条件とする。
2. **障害時ロールバック手順**:
   - 一時障害・軽微なデプロイミス時は、`workflow_dispatch` で再トリガーまたは直前正常コミットからの再デプロイを行う。
   - 本番障害時は、Firebase Hosting CLI (`firebase hosting:rollback`) により即時に前バージョンへ切り戻す。

---

## 3. DBバックアップ & DR (災害復旧) 運用方針（T870 / R116）

### 3.1 本番DBバックアップCI復旧 (`docs/SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md`)
- **障害要因 (R116) 解消**: GCP Workload Identity Federation (WIF) の設定（`roles/iam.workloadIdentityUser` へのロール修正、Attribute Condition によるリポジトリ制限、現行 GCP プロジェクト Number 指定）を実施。
- **保存先 & セキュリティ**: GCS Private Bucket (`--public-access-prevention` 有効) へ保存。Secret (`SUPABASE_DB_URL` / `SUPABASE_BACKUP_GCS_URI` 等) は対話入力で登録し、リポジトリ・ドキュメント上に秘匿値を露出させない。
- **実行頻度 & 保持**: 毎日 03:00 JST (`0 18 * * *`) 実行、保持世代数 7 代 (`SUPABASE_BACKUP_RETENTION: "7"`).

### 3.2 DR (災害復旧・リストア) ポリシー
- **目標仕様**: RPO = 24時間 / RTO = 手動リストア完了 2時間以内
- **定期リストア演習**: 月1回、検証環境（Staging / Local Docker DB）へのダンプデータ復旧演習を実施し、[SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) の最新性を維持・検証する。

---

## 4. SLA 計測 & 本番稼働モニタリング方針（T778）

### 4.1 SLA 目標指標 (KPI)
- **サービス稼働率 (Uptime)**: **99.5 % 以上**
- **P95 レスポンスタイム**: **3,000 ms 以内**
- **診断評価精度ヘルプフル率**: **70 % 以上**

### 4.2 モニタリング & アラーティング
- **リアルタイムヘルスチェック**: `.github/workflows/uptime-monitor.yml` により 30 分周期でエンドポイント稼働を監視。障害検知時は Slack チャンネル (`SLACK_WEBHOOK_URL`) へ即時アラート送信。
- **SLA レポート集計**: Supabase ビュー (`uptime_checks` ＋ 6 ビュー) および `scripts/generate_sla_measurement_report.py` を活用し、週次・月次で SLA 指標を自動測定して PM（梅澤）および開発チームへ共有する。

---

## 5. クラウドコスト管理 & 予算超過警告方針 (`weekly-cost-dashboard.yml`)

### 5.1 コスト管理・アラート閾値
- **注意アラート (Warning)**: 月額予算の消化率 **80% 到達時** に Slack へ自動警告。
- **緊急アラート (Critical)**: 月額予算の消化率 **100% 超過時** に Slack へ即時緊急アラート送信。

### 5.2 コストダッシュボード報告
- 毎週月曜日 08:15 JST に `generate_weekly_cost_dashboard.py` を実行し、`exports/weekly_cost_dashboard.md` レポートを自動生成。開発チーム・PM・経営定例資料へ共有。

---

## 6. ログ保持 & セキュリティ Secret ローテーション方針

### 6.1 ランタイムログ保持 (`runtime-log-retention.yml` / `rotate_runtime_logs.py`)
- FastAPI / Uvicorn / アプリケーションランタイムログは **30 日間保持**。
- 週次で過去 30 日を超過したログを自動パージし、ストレージ容量を最適化する。

### 6.2 Secret ローテーション監査 (`secret-rotation-review.yml` / `check_secret_rotation_schedule.py`)
- GitHub Secrets / API キー / Service Account Key は **90 日ごとの定期ローテーション** を義務化。
- 週次 CI ジョブで有効期限・更新猶予を自動チェックし、更新期限超過時はビルドエラーを発行してセキュリティ担当（山田 太郎）と連携・即時更新する。

---

## 7. Supabase DB パフォーマンス診断 & インデックス運用 (`supabase-performance-diagnostic.yml` / T881)

### 7.1 定期パフォーマンス診断
- 毎週月曜日 05:45 JST に `diagnose_supabase_performance.py` および `generate_supabase_query_performance_review.py` を自動実行。
- P95 レスポンスタイム **> 1,000 ms** のスロークエリを常時監視・検知。

### 7.2 FK インデックス被覆監査 (T881)
- `scripts/audit_fk_index_coverage.py` を継続実行し、製品マイグレーション (`supabase/migrations/`) の全外部キー (FK) 列がインデックスで被覆されているか機械照合（未被覆ギャップ 0 を自動維持）。

---

## 8. ガード & 健全性維持

- **Public Demo Guard** (`scripts/verify_public_demo.py` / `public-demo-guard.yml`): デモサイトの常時正常稼働を保証。
- **レーンプリフライト** (`scripts/run_lane_preflight.py`): コミット・プッシュ前に全 23 件の整合ガードを検証し、ドリフト 0 を維持。
