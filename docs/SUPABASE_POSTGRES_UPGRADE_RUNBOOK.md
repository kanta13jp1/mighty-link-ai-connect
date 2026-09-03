# Supabase Postgres 14 EOL 対応 Runbook

更新日: 2026-06-21  
担当レーン: Codex  
関連WBS: T828 / T811  
関連Issue: #119 / #80 / R53

## 目的

Supabase は Postgres 14 のサポートを 2026-07-01 に終了する。Mighty-Link AI Connect の staging / production が Postgres 14 のまま残ると、セキュリティ修正、互換性、強制アップグレード時の停止リスクが高くなる。

このRunbookは、DB接続情報やservice role keyを記録せずに、staging / production のPostgresメジャーバージョン確認、PG14検知、アップグレード前チェック、アップグレード後検証を標準化する。

## 公式Docs確認

2026-06-21時点で以下を確認した。

- Supabase changelog: Postgres 14 support is deprecated and removed on 2026-07-01.
- Supabase Docs: Postgres versionはSQL Editorまたはpsqlで `select version();` を実行して確認する。
- Supabase Docs: Postgresアップグレードはin-place upgradeまたはpause and restoreで実施する。通常はin-place upgradeが推奨される。
- Supabase Docs: アップグレード時はlogical replication slot、古いTimescaleDB/plv8、Postgres 17でdeprecatedのextensions、pg_graphql 1.6.0のintrospection変更、md5認証方式の非推奨に注意する。

## Secretルール

- `SUPABASE_STAGING_DB_URL`、`SUPABASE_PROD_DB_URL`、service role key、DB passwordはGitHub、Issue、Sheets、docs、NotebookLM、Slack、チャット本文へ記録しない。
- 接続URLはローカル環境変数、GitHub Actions Secrets、または会社指定のSecret管理経路で扱う。
- 生成レポートにはredacted URLと `version()` のメジャーバージョンだけを残す。

## バージョン確認

環境変数がある場合:

```powershell
$env:SUPABASE_STAGING_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
$env:SUPABASE_PROD_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
python scripts/check_supabase_postgres_version.py --execute
```

Dashboard SQL Editorで手動確認する場合:

```sql
select version();
```

結果はsecretを含まない `PostgreSQL 15.1 ...` のような文字列だけを使い、次のようにレポート化する。

```powershell
python scripts/check_supabase_postgres_version.py --dry-run `
  --offline-version "staging=PostgreSQL 15.1 on aarch64-unknown-linux-gnu" `
  --offline-version "production=PostgreSQL 15.1 on aarch64-unknown-linux-gnu"
```

出力:

- `exports/supabase_postgres_version_check.json`
- `exports/supabase_postgres_version_check.md`

## 判定

| 結果 | 判定 | 次アクション |
| --- | --- | --- |
| staging / production とも Postgres 15以上 | T811の実接続確認はOK。通常のアップグレード監視へ戻す | R53を解決し、WBS/Sheetsへ記録 |
| どちらかが Postgres 14 | critical | stagingを先にアップグレードし、検証後にproductionのメンテナンスウィンドウを確保 |
| 接続情報なし | needs_credentials | secretを貼らず、会社管理経路でDB URLを受け取り再実行 |
| `version()`がparse不能 | warning | SQL Editorで再確認し、Postgresのメジャーバージョンだけを再記録 |

## PG14だった場合のアップグレード前ゲート

1. Supabase Dashboardで最新backupまたはPITR時刻を記録する。
2. `python scripts/backup_supabase_database.py --dry-run --skip-upload` で論理backup手順を確認する。
3. stagingで先にアップグレードする。productionを先に変更しない。
4. logical replication slotを使っている場合、アップグレード後に再作成が必要か確認する。
5. TimescaleDB、plv8、pg_graphql、pgjwt、Postgres 17でdeprecatedのextensionを確認する。
6. pg_graphql 1.6.0へ上がる場合、GraphQL introspection依存がないか確認する。
7. md5認証方式に依存した古いクライアントがないか確認する。
8. productionは利用が少ない時間帯にメンテナンスウィンドウを取り、CEO/運用担当へ事前共有する。

## アップグレード後検証

staging / production それぞれで実施する。

```powershell
python scripts/check_supabase_postgres_version.py --execute
python scripts/manage_db_migrations.py validate --engine supabase
python -m pytest tests/test_sales_email_schema_migrations.py tests/test_supabase_postgres_version_check.py
python scripts/verify_public_demo.py --url https://mightylink-app.com/
```

必要に応じて以下も確認する。

- Firebase Functions / Cloud Run からSupabaseへの接続
- Supavisor poolerのtransaction/session mode
- RLS policyと匿名REST直アクセスの拒否
- 営業メールAIマッチングDBの読み書き
- backup / restore Runbookの復旧手順

## 今回の状態

2026-06-21のT828では、実DB URLがローカル環境に未設定だったため、staging / production の実接続確認は行っていない。代わりに、T811の実作業で迷わず確認できるスクリプト、Runbook、pytest、secret非出力レポートを整備した。

T811では、会社指定のSecret管理経路で `SUPABASE_STAGING_DB_URL` と `SUPABASE_PROD_DB_URL` を受け取り、`--execute` またはDashboard SQL Editorのoffline-versionで最終確認する。

