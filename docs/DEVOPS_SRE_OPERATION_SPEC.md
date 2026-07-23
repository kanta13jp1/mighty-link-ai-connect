# DevOps / SRE 運用仕様書 & アーキテクチャ決定（T896, T870, T778）

作成日: 2026-07-23  
担当責任者: **DevOps / SRE スペシャリスト（鈴木 一郎）**  
対象領域: クラウドインフラ（Firebase/GCP/Supabase）、GitHub Actions CI/CD、DBバックアップ、SLA/DR

---

## 1. 概要 & 基本方針

本ドキュメントは、Mighty Link AI Connect プロジェクトにおける DevOps / SRE 領域の基本方針、CI/CD デプロイ制御、DBバックアップ・災害復旧（DR）運用、および SLA/稼働モニタリング設計を定めた仕様書です。

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

## 5. ガード & 健全性維持

- **Public Demo Guard** (`scripts/verify_public_demo.py` / `public-demo-guard.yml`): デモサイトの常時正常稼働を保証。
- **レーンプリフライト** (`scripts/run_lane_preflight.py`): コミット・プッシュ前に全 23 件の整合ガードを検証し、ドリフト 0 を維持。
