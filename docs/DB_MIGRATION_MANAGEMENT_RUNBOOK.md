# DBマイグレーション管理 Runbook

## 目的

Mighty Skill-Bridge の DB スキーマ変更を、Git 管理された migration と検証ログに集約する。対象は Supabase/PostgreSQL 本番・staging と、ローカル/CI の SQLite fallback。

## 正本

- Supabase product-domain schema: `supabase/migrations/`
- アプリ実行時 schema: `db/migrations/postgres/`
- ローカル fallback schema: `db/migrations/sqlite/`
- 適用・検証スクリプト: `scripts/manage_db_migrations.py`
- ロールバック方針: `docs/PRODUCTION_ROLLBACK_RUNBOOK.md`

## 基本方針

1. 本番・staging のリモートDBを直接変更しない。
2. 共有DBへ適用済みの migration は編集しない。修正は forward-fix migration を追加する。
3. migration file名は `YYYYMMDDHHMMSS_short_slug.sql` に統一する。
4. 本番適用は1レーンだけが実行し、実行前に backup/PITR 時刻・Issue・WBS を記録する。
5. 破壊的変更は staging で復元手順を確認してから実行する。

## 通常フロー

### 1. migrationを作成

Supabase CLI 管理対象は公式フローに合わせる。

```powershell
supabase migration new add_example_column
```

アプリ実行時 schema は engine 別に追加する。

```powershell
# 例
New-Item db/migrations/postgres/20260615090000_add_example_column.sql
New-Item db/migrations/sqlite/20260615090000_add_example_column.sql
```

### 2. ローカル検証

```powershell
python scripts/manage_db_migrations.py validate --engine sqlite
python scripts/manage_db_migrations.py validate --engine postgres
python scripts/manage_db_migrations.py validate --engine supabase
python scripts/manage_db_migrations.py apply --engine sqlite --sqlite-path data/mighty.db --dry-run
python -m pytest tests/test_db_migration_management.py tests/test_rls_policies.py
```

`--dry-run` は pending/applied/checksum mismatch の計画だけを表示する。実際に SQLite へ適用する場合は `--dry-run` を外す。

### 3. staging適用

```powershell
python scripts/verify_staging_environment_config.py --fail-on-critical
supabase migration list --linked
supabase db reset
supabase db push
python -m pytest
```

Supabase migration history と Git の migration file がずれた場合は、`supabase migration list` で差分を確認し、実DB状態が正しいことを確認してから `supabase migration repair` を使う。`repair` は履歴修正だけであり、SQLの巻き戻しには使わない。

### 4. production適用

1. `scripts/backup_supabase_database.py` または Supabase Dashboard の backup/PITR 時刻を記録する。
2. 対象 Issue に migration version と判断者を書く。
3. one-lane lock を宣言し、並行pushを止める。
4. `supabase migration list --linked` で差分を確認する。
5. `supabase db push` を実行する。
6. API smoke test、RLS test、public demo guard を実行する。
7. WBS/Sheets/Calendar/GitHub Project を同期する。

## CI

`.github/workflows/db-migration-validate.yml` が以下を検証する。

- `db/migrations/sqlite/` の命名・重複version・SQL statement検出
- `db/migrations/postgres/` の命名・重複version・SQL statement検出
- `supabase/migrations/` の命名・重複version・SQL statement検出
- SQLite migration runner の idempotency pytest

## 障害時

- 軽微な schema 誤り: forward-fix migration を追加する。
- data loss 可能性あり: 書き込み停止、backup/PITR、復元先DBで検証、本番復元または補正migration。
- migration history だけがずれた: 実DB状態を確認し、Issueに証跡を残してから `supabase migration repair`。

## 公式ドキュメント確認メモ

- Supabase Database Migrations: `supabase migration new`、`supabase db reset`、`supabase db push`、チーム開発時の「リモートDB直接変更禁止」を正本にする。
- Firebase Functions/Hosting: environment と custom domain SSL は本番接続に影響するため、DB migration と同じ closeout で公開URL guardを通す。
- GitHub Actions: migration validation は PR/push/workflow_dispatch で自動実行する。
