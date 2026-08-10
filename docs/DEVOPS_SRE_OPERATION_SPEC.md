# DevOps / SRE 運用仕様書 & アーキテクチャ決定（T896, T870, T778, コスト, ログ, パフォーマンス, GA判定, BCP）

作成日: 2026-07-23  
最終更新日: 2026-07-24 (大障害BCP・フェイルオーバー規定追加)  
担当責任者: **DevOps / SRE スペシャリスト（鈴木 一郎）**  
対象領域: クラウドインフラ（Firebase/GCP/Supabase）、GitHub Actions CI/CD、DBバックアップ、SLA/DR、コスト管理、セキュリティ鍵運用、DBパフォーマンス、GA判定、BCP

---

## 1. 概要 & 基本方針

本ドキュメントは、Mighty Link AI Connect プロジェクトにおける DevOps / SRE 領域の基本方針、CI/CD デプロイ制御、DBバックアップ・災害復旧（DR）運用、SLA/稼働モニタリング設計、クラウドコスト管理、ログ・Secretローテーション、DB パフォーマンス診断、GA リリース判定基準、障害一次対応体制、ならびに大障害時の BCP（事業継続計画）・フェイルオーバー方針を定めた包括的運用仕様書です。

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
- **リアルタイムヘルスチェック**: `.github/workflows/uptime-monitor.yml`（Production Operations Monitor）により15分周期でエンドポイント稼働を監視。同workflowの別jobで営業メールも読み取り専用取得する。障害検知時は Slack チャンネル (`SLACK_WEBHOOK_URL`) へ即時アラート送信。
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

## 8. GA リリース Go/No-Go 判定基準 & 障害一次対応体制 (T849 / T850)

### 8.1 SRE 観点での GA リリース Go/No-Go 判定基準
以下の 3 条件がすべて満たされていることを SRE としての Go 判定条件とする：
1. **本番 DB バックアップ CI (T870) 成功**: Supabase Daily Backup ジョブが本番 GCS バケットへ正常にダンプを作成できていること。
2. **Production Operations Monitor 正常稼働**: 過去24時間のヘルスチェック成功率100%、営業メール同期job失敗0件。
3. **全 24 件の整合プリフライトガード PASS**: ドリフト 0 を維持していること。

### 8.2 障害一次対応 (ファーストレスポンス・オンコール体制)
- リアルタイムアラート（Slack / GitHub Actions）検知時、**SRE (鈴木 一郎)** がファーストレスポンスとして一次対応を実施。
- ログ解析 (`GCP Cloud Logging`, `Supabase Logs`, `rotate_runtime_logs.py`) により原因を特定し、インフラ障害時は即時切り戻し (Firebase Rollback / 再デプロイ)、アプリ層・DB層障害時は該当リード (佐藤 / さかい / 古屋) へ速やかに切り分ける。

---

## 9. 大障害 BCP (事業継続計画) & フェイルオーバー方針

### 9.1 大障害時の切り替え体制
1. **フロントエンド障害時**: Firebase Hosting 障害時は、DNS 保持切り替えにより独立稼働する GitHub Pages 環境（`https://kanta13jp1.github.io/mighty-link-ai-connect/`）上の静的メンテナンス・状況告知ページへルーティングを変更。
2. **データベース大規模障害時**: Supabase メインリージョン障害時は、GCS Private Bucket に保存された最新日次バックアップ（RPO 24h）から代替 Postgres インスタンスへリカバリ（RTO 2時間以内）を実施し、API 接続先 (`SUPABASE_DB_URL`) を切り替える。
