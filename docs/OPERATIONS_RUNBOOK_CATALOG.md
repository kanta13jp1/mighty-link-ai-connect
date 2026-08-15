# 運用Runbookカタログ（索引） / Operations Runbook Catalog

作成日: 2026-07-19 / 担当レーン: VSCode + Claude Code（T902）
正本: 本ファイルが運用Runbookの唯一の索引。`scripts/audit_runbook_catalog.py`（T902）が`docs/*RUNBOOK*.md` の実ファイル集合と本カタログの掲載集合を毎回照合し、**孤児（未掲載）・切れリンク（実体なし）をゼロに保つ**。
関連WBS: 全運用Runbook / T810（インシデント）/ T812（ロールバック）/ T850（引継ぎ）/ T849（GA完了判定）

> [!IMPORTANT]
> **インシデント時はまず本カタログで状況→該当Runbookを引く。** 新規Runbookを追加したら必ず本カタログの該当カテゴリへ1行追加すること（未追加はCIガードが孤児として検知して失敗する）。

- 運用Runbook総数: **46本**（9カテゴリ）

---

## DB・データ基盤

- [Supabase DB バックアップ・リストア運用 Runbook（T741)](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) — DBのバックアップ取得・復旧が必要なとき
- [Supabase Daily Backup CI 復旧 Runbook（T870 / R116)](SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md) — バックアップCIが失敗し続けるとき（WIF再構成・バケット作成・secret登録・green確認）
- [Supabase 接続プール運用 Runbook（T759)](SUPABASE_CONNECTION_POOLING_RUNBOOK.md) — 接続数枯渇・プール設定を見直すとき
- [Supabase Postgres 14 EOL 対応](SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md) — Postgresメジャー/EOL対応を行うとき
- [Supabase クエリ性能ダッシュボード運用 Runbook（T761)](SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md) — クエリが遅い・性能を監視するとき
- [DBマイグレーション管理](DB_MIGRATION_MANAGEMENT_RUNBOOK.md) — スキーマ変更・migration適用を行うとき
- [パフォーマンス診断・DBインデックス最適化 Runbook（T750)](PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md) — 応答が遅い・インデックスを最適化するとき

## インフラ・監視・インシデント対応

- [本番インフラ障害 エスカレーション連絡網・ディザスタリカバリ（DR）運用計画書（T749)](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) — 本番インフラ障害・DR発動・連絡網が必要なとき
- [障害インシデント対応記録・ポストモーテム運用 Runbook（T810)](INCIDENT_POSTMORTEM_RUNBOOK.md) — インシデント記録・ポストモーテムを書くとき
- [本番リリース ロールバック手順書（T812)](PRODUCTION_ROLLBACK_RUNBOOK.md) — リリースを切り戻すとき
- [本番死活監視・Slackアラート Runbook（T743)](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md) — 死活監視・Slackアラートを設定/対応するとき
- [インフラ・テレメトリ監視ダッシュボード Runbook（T755)](INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md) — インフラ状態を可視化・監視するとき
- [Firebase / Supabase クォータ・エラー監視アラート Runbook（T761_1)](FIREBASE_SUPABASE_QUOTA_ERROR_ALERT_RUNBOOK.md) — クォータ超過・エラー急増を検知したとき
- [API レート制限・DDoS 緩和](API_RATE_LIMIT_AND_DDOS_RUNBOOK.md) — APIレート制限・DDoS緩和が必要なとき
- [AIモデル・外部SaaS・連携サービス GA凍結](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md) — AI/外部SaaS連携を緊急凍結するとき
- [Firebase / Supabase ステージング環境運用 Runbook（T788)](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md) — ステージング環境を運用・検証するとき
- [Firebase Emulator / Supabase Local 開発環境 Runbook（T760)](LOCAL_DEV_EMULATOR_STACK_RUNBOOK.md) — ローカルでエミュレータ開発するとき

## セキュリティ・鍵・ログ管理

- [四半期セキュリティ監査ランブック（T774)](SECURITY_AUDIT_RUNBOOK.md) — 四半期セキュリティ監査を行うとき
- [外部ペネトレーション疑似診断Runbook（T805)](EXTERNAL_PENTEST_RUNBOOK.md) — 外部脆弱性/疑似診断を行うとき
- [サードパーティAPIキー・Secretローテーション Runbook（T751)](SECRET_ROTATION_RUNBOOK.md) — APIキー・Secretをローテーションするとき
- [ログローテーション・アクセスログ保持 Runbook（T748)](LOG_ROTATION_AND_RETENTION_RUNBOOK.md) — ログ保持/ローテーションを運用するとき
- [監査ログ・稼働ログ コールドストレージ退避 Runbook（T773)](COLD_STORAGE_LOG_ARCHIVE_RUNBOOK.md) — 古い監査/稼働ログを退避するとき
- [セキュリティインシデント対応・ログ健全性運用Runbook（T931)](SECURITY_INCIDENT_RESPONSE_RUNBOOK.md) — セキュリティ違反・不正アクセス・ログ健全性異常を検知したとき

## 課金・コスト

- [経理・税務・コスト管理 Runbook（T813/T823)](ACCOUNTING_AND_TAX_OPERATIONS_RUNBOOK.md) — 経理・インボイス・税務処理・コスト監査を行うとき
- [Stripe Customer Portal](STRIPE_CUSTOMER_PORTAL_RUNBOOK.md) — 解約/プラン変更のCustomer Portalを扱うとき
- [週次課金・コスト配分ダッシュボード Runbook（T757)](WEEKLY_COST_DASHBOARD_RUNBOOK.md) — 週次のコスト配分を確認するとき

## コンプライアンス・データ主体対応

- [本番データ保持・削除・匿名化ポリシー全テーブル照合](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md) — 保持/削除/匿名化ポリシーを照合するとき
- [ユーザーデータセルフエクスポート](USER_DATA_SELF_EXPORT_RUNBOOK.md) — 利用者のデータ開示/持ち出し要求に応じるとき
- [利用規約・プライバシーポリシー同意UI/API Runbook（T745)](LEGAL_CONSENT_UI_AND_API_RUNBOOK.md) — 規約/プライバシー同意導線を扱うとき
- [社内向け適性・状況アンケート回答保存](EMPLOYEE_ASSESSMENT_RESPONSE_RUNBOOK.md) — 適性/状況アンケート回答保存を扱うとき

## 営業メールAI

- [営業メール取り込みPoC](SALES_EMAIL_INGESTION_POC_RUNBOOK.md) — 営業メール取り込みを検証するとき
- [営業メールAI抽出パイプライン](SALES_EMAIL_EXTRACTION_PIPELINE_RUNBOOK.md) — 営業メールAI抽出パイプラインを扱うとき
- [営業メールAIマッチング DBスキーマ](SALES_EMAIL_DATABASE_SCHEMA_RUNBOOK.md) — 営業メールのDBスキーマを扱うとき
- [営業メールAIマッチング 人間レビュー・評価ログ](SALES_EMAIL_HUMAN_REVIEW_RUNBOOK.md) — 営業メールの人間レビュー/評価ログを扱うとき
- [営業メールAIマッチング検索API/UI](SALES_EMAIL_MATCHING_API_UI_RUNBOOK.md) — 営業メールマッチング検索API/UIを扱うとき

## 運用・引継ぎ・アカウント移行

- [会社運用引継ぎリハーサル・Break-glass ランブック（T850）](OPERATIONS_HANDOVER_REHEARSAL_RUNBOOK.md) — 会社運用の引継ぎ/Break-glassを演習するとき
- [会社アカウント移行準備](ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md) — 会社アカウントへ本移管するとき
- [Google Workspace 移行・共有作業手順書](GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md) — Google Workspace移行/共有作業のとき
- [Google Workspace OAuth 再認証](GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md) — Google OAuth再認証が必要なとき

## リリース・同期・レポート・モデル追従

- [リリースノート・バージョニング運用](RELEASE_VERSIONING_RUNBOOK.md) — リリースノート/バージョニングを運用するとき
- [GitHub Issues / Project WBS 同期](GITHUB_WBS_SYNC_RUNBOOK.md) — WBSをGitHub Issues/Projectへ同期するとき
- [月次品質レポート自動配信 Runbook（T808)](MONTHLY_QUALITY_REPORT_DELIVERY_RUNBOOK.md) — 月次品質レポートを配信するとき
- [NotebookLM 同期タイムアウト対策](NOTEBOOKLM_SYNC_TIMEOUT_RUNBOOK.md) — NotebookLM同期がタイムアウトするとき
- [Gemini APIモデル追従・移行](GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md) — Geminiモデルを追従/移行するとき

## プロダクト運用・利用者対応

- [管理者向け統合ダッシュボード](ADMIN_OPERATIONS_DASHBOARD_RUNBOOK.md) — 管理者ダッシュボードを運用するとき
- [勤務表自動解析・勤怠承認ワークフロー](ATTENDANCE_WORKFLOW_RUNBOOK.md) — 勤務表解析/勤怠承認を扱うとき
- [T800 利用状況アナリティクス計測設計・運用](USAGE_ANALYTICS_KPI_RUNBOOK.md) — 利用状況アナリティクスを計測するとき
- [User Feedback Collection Runbook（T763)](USER_FEEDBACK_COLLECTION_RUNBOOK.md) — 利用者フィードバックを収集するとき
- [Support Contact and Escalation Runbook（T790)](SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md) — 問い合わせ一次対応/エスカレーションのとき

