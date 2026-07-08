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
6. **DDLの正本は `supabase/migrations/` に一本化する（T866/R114）**。`src/app.py` の `init_db` はコールドスタート時のスキーマ保証（レガシーテーブル+SQLite fallback）であり、新規テーブルのDDLをinit_dbだけに書くことは禁止。新機能テーブルは必ずmigrationファイルとして追加する。

## 新規テーブル追加チェックリスト（T866/R114 再発防止）

新しいテーブル・列を追加するタスクは、以下を完了条件に含める。

- [ ] `supabase/migrations/YYYYMMDDHHMMSS_*.sql` を追加した（DDL正本）。
- [ ] RLS有効化と `anon, authenticated` の REVOKE を同じmigrationに含めた。
- [ ] **本番適用の実施証跡**（適用日時・実行者・適用後のテーブル数/カラム確認結果）を Issue または WBS 備考へ記録した。「検証のみのCI」green は適用証跡にならない（R114教訓）。
- [ ] 適用直後に該当機能の本番POST/SELECTを1件実行し、保存成功を確認した。
- [ ] ビュー/レポートが参照する列は `scripts/verify_sla_measurement_views.py` 型のドリフトガードまたはテストで固定した。

補足（T866実装済みの保険）: `lifespan` は `yield` 前に `init_db` を完走させるため、コールドスタート直後の初回リクエストでスキーマ未初期化500は発生しない。またストレージ系insert失敗は `record_storage_failure` が `relation_missing / connection / constraint / unknown` に分類し、相関ID付きでログと500 detailへ出力する（SQL文・個人データはクライアントへ出さない）。migration未適用が再発した場合、500 detailの `category=relation_missing` が即座に根本原因を指す。

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

## 営業メールAIマッチング migration

T817_3で営業メールAIマッチング用の `20260618000000_sales_email_matching_schema` を追加した。詳細は `docs/SALES_EMAIL_DATABASE_SCHEMA_RUNBOOK.md` を正本にする。

- Supabase: `supabase/migrations/20260618000000_sales_email_matching_schema.sql`
- PostgreSQL runtime: `db/migrations/postgres/20260618000000_sales_email_matching_schema.sql`
- SQLite fallback: `db/migrations/sqlite/20260618000000_sales_email_matching_schema.sql`
- rollback: `db/migrations/rollback/20260618000000_sales_email_matching_schema_rollback.sql`
- test: `tests/test_sales_email_schema_migrations.py`

このmigrationはメール本文全文、OAuth token、service role secretを保存しない。Supabase側では全テーブルでRLSを有効化し、`anon` と `authenticated` の直接アクセスを `REVOKE ALL` する。T817_5の候補検索APIはsanitized extraction reviewを読むだけでDBへ匿名REST直書きしない。T817_6の人間レビュー保存はBasic Auth付きサービスAPI経由に限定し、公開REST用の `CREATE POLICY` はT817_7の実メールDB運用hardening時に必要最小限で追加する。

## 障害時

- 軽微な schema 誤り: forward-fix migration を追加する。
- data loss 可能性あり: 書き込み停止、backup/PITR、復元先DBで検証、本番復元または補正migration。
- migration history だけがずれた: 実DB状態を確認し、Issueに証跡を残してから `supabase migration repair`。

## 公式ドキュメント確認メモ

- Supabase Database Migrations: `supabase migration new`、`supabase db reset`、`supabase db push`、チーム開発時の「リモートDB直接変更禁止」を正本にする。
- Supabase Row Level Security: テーブル単位でRLSを有効化し、公開REST/APIのポリシーは最小権限で明示的に追加する。
- Firebase Functions/Hosting: environment と custom domain SSL は本番接続に影響するため、DB migration と同じ closeout で公開URL guardを通す。
- GitHub Actions: migration validation は PR/push/workflow_dispatch で自動実行する。
