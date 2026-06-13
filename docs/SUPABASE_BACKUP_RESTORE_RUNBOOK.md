# Supabase DB バックアップ・リストア運用 Runbook (T741)

作成日: 2026-06-13  
担当レーン: VSCode + Codex  
対象: Mighty Skill-Bridge / Mighty-Link AI Connect 本番 Supabase PostgreSQL

## 目的

本番 DB の日次バックアップ、7世代保管、GCS 退避、復元手順を標準化する。RPO は 24 時間、RTO は 2 時間を目標にする。Supabase Dashboard の自動バックアップ / PITR と、このリポジトリの論理 dump を組み合わせて、破壊的 migration や本番障害に備える。

## 公式ドキュメント確認

2026-06-13 に以下を確認した。

- Supabase Database Backups: Dashboard からの日次バックアップと復元、PITR の扱い
- Supabase CLI Backup and Restore: `supabase db dump` と `psql --single-transaction` による復元
- Supabase Database Overview: Backups は DB 対象で、Storage API オブジェクトは別管理
- GitHub Actions: scheduled workflow / workflow_dispatch / repository secrets
- Google Cloud: Workload Identity Federation と GCS 転送

## 対象範囲

対象:

- Supabase PostgreSQL の role / schema / data 論理 dump
- 毎日 03:00 JST の GitHub Actions 定期実行
- GCS への外部退避
- ローカル作業時の dry-run と復元コマンド検証

対象外:

- Supabase Storage オブジェクト
- Firebase Auth ユーザー export
- NotebookLM / Google Drive / Sheets のバックアップ

## 必要な GitHub Secrets

| Secret | 用途 |
| --- | --- |
| `SUPABASE_DB_URL` | 本番 Supabase Postgres の接続文字列 |
| `SUPABASE_BACKUP_GCS_URI` | `gs://bucket/path` 形式の退避先 |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | GitHub Actions から GCP へ WIF 認証する provider |
| `GCP_SERVICE_ACCOUNT_EMAIL` | GCS 書き込み権限を持つ service account |

`SUPABASE_DB_URL` は絶対に docs / data / issue 本文へ貼らない。スクリプトと manifest はパスワードを `***` にマスクする。

## バックアップ

GitHub Actions:

- Workflow: `.github/workflows/supabase-backup.yml`
- Schedule: `0 18 * * *` UTC = 03:00 JST
- Retention: ローカル一時領域 7 世代、GCS 側の lifecycle は bucket policy で管理

手動 dry-run:

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
python scripts/backup_supabase_database.py --dry-run --skip-upload
```

本番手動実行:

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
$env:SUPABASE_BACKUP_GCS_URI = "gs://<private-bucket>/supabase"
python scripts/backup_supabase_database.py
```

生成物:

- `roles.sql`
- `schema.sql`
- `data.sql`
- `manifest.json`

`backups/` は `.gitignore` 済み。バックアップ SQL はリポジトリへ commit しない。

## リストア

原則として、既存 production へ直接復元する前に「新規 Supabase project へ復元して検証」する。production 直接復元は P1 / P2 障害時のみ、人間の Go/No-Go を通す。

dry-run:

```powershell
$env:SUPABASE_RESTORE_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
python scripts/restore_supabase_database.py backups/supabase/20260613T180000Z --dry-run
```

実復元:

```powershell
$env:SUPABASE_RESTORE_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
python scripts/restore_supabase_database.py backups/supabase/20260613T180000Z --confirm-restore
```

復元後確認:

```powershell
python -m pytest tests/test_rls_policies.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

## 運用チェックリスト

- GitHub Actions の `Supabase Daily Backup` が毎日成功している
- `manifest.json` に秘密情報が出ていない
- GCS bucket は private、versioning / lifecycle / retention policy を設定済み
- 破壊的 migration 前に直近 backup / PITR 時刻を記録する
- 半年に1回、復元訓練を新規 Supabase project で行う

## 関連ドキュメント

- [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md)
- [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md)
- [WBS.md](WBS.md)
