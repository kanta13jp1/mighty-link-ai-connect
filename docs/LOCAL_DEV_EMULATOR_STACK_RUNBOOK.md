# Firebase Emulator / Supabase Local 開発環境 Runbook (T760)

作成日: 2026-06-15  
担当レーン: Codex  
関連: [FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md) / [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md) / [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md)

## 目的

Firebase Hosting / Auth / Functions と Supabase PostgreSQL をローカルだけで起動し、production の Firebase project、Supabase DB、service role key、実ユーザーデータに触れずに統合テストできる状態を標準化する。

T760 の完了条件は次の4点。

- `firebase.json` に Auth / Functions / Hosting / Emulator UI の固定ポートを定義する。
- `supabase/config.toml` と `supabase/seed.sql` をローカル開発用に整備し、seed は合成データだけにする。
- `scripts/verify_local_dev_stack.py` と pytest で設定・seed・secret混入を検証できる。
- GitHub Actions の `Local Dev Stack Validation` で PR/push 時に同じ検証を走らせる。

## 公式 Docs 確認メモ

2026-06-15 の作業開始時に、Firebase Emulator Suite、Supabase Local CLI、GitHub Actions の公式Docsを確認した。反映した運用ルールは次のとおり。

- Firebase Emulator Suite は `firebase.json` の `emulators` 設定を正とし、Auth / Functions / Hosting / UI のポートを固定する。
- Supabase CLI は `supabase init` で生成される `supabase/config.toml` をGit管理し、`supabase start` で API `54321`、DB `54322`、Studio `54323` を使う。
- Supabase local は Docker コンテナで動くため、ローカル検証は Docker Desktop または互換ランタイムが前提。
- secret は config に直書きせず、必要時は環境変数参照にする。production URL / service role key はローカル統合テストの前に必ず外す。
- GitHub Actions では Docker/Firebaseを起動しない静的検証を先に通し、重い統合テストは明示的な workflow_dispatch またはローカルで実行する。

## 固定ポート

| サービス | URL / ポート | 用途 |
| --- | --- | --- |
| Firebase Emulator UI | `http://127.0.0.1:4000` | Auth / Functions / Hosting のローカル状態確認 |
| Firebase Hosting Emulator | `http://127.0.0.1:5000` | 静的ファイルと Hosting rewrite の確認 |
| Firebase Functions Emulator | `http://127.0.0.1:5001` | API / Cloud Functions のローカル確認 |
| Firebase Auth Emulator | `http://127.0.0.1:9099` | 認証フローのローカル確認 |
| Supabase API | `http://127.0.0.1:54321` | REST / GraphQL / Auth API |
| Supabase PostgreSQL | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` | ローカルDB |
| Supabase Studio | `http://127.0.0.1:54323` | DBテーブル・seed確認 |

## 初回セットアップ

```powershell
# Node.js 20+ と Firebase CLI / Supabase CLI / Docker Desktop が前提
firebase --version
supabase --version
docker version

# 設定の静的検証
python scripts/verify_local_dev_stack.py --fail-on-critical

# DB migration と T760 検証テスト
python scripts/manage_db_migrations.py validate --engine supabase
python -m pytest tests/test_local_dev_stack.py tests/test_db_migration_management.py tests/test_rls_policies.py
```

Supabase CLI を `npx` 経由で使う場合は Node.js 20 以上が必要。グローバル `npm install -g supabase` は使わず、Scoop / standalone binary / `npx supabase` を使う。

## 起動手順

PowerShell で production DB URL が残っていないことを確認してから起動する。

```powershell
Remove-Item Env:SUPABASE_DB_URL -ErrorAction SilentlyContinue
python scripts/verify_local_dev_stack.py --check-env --fail-on-critical

supabase start
firebase emulators:start --only auth,functions,hosting
```

別ターミナルでAPIやUIのテストを実行する。

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
$env:FIREBASE_AUTH_EMULATOR_HOST = "127.0.0.1:9099"

python -m pytest tests/test_api.py tests/test_rls_policies.py
```

終了時は次を実行する。

```powershell
supabase stop
Remove-Item Env:SUPABASE_DB_URL -ErrorAction SilentlyContinue
Remove-Item Env:FIREBASE_AUTH_EMULATOR_HOST -ErrorAction SilentlyContinue
```

## 検証スクリプト

`scripts/verify_local_dev_stack.py` は次を確認する。

- `firebase.json` / `.firebaserc` が読める。
- Firebase Emulator の固定ポートが `9099` / `5001` / `5000` / `4000` である。
- `singleProjectMode` が有効である。
- `supabase/config.toml` が読め、`project_id` が production 名ではない。
- Supabase API / DB / Studio の固定ポートが `54321` / `54322` / `54323` である。
- `supabase/seed.sql` が存在し、`example.test` の合成データだけを使っている。
- local stack config に secret-like な値が含まれていない。
- `--check-env` 指定時、`SUPABASE_DB_URL` が未設定または `127.0.0.1:54322` を指している。

レポートは `exports/local_dev_stack_report.json` に出力される。

## CI

`.github/workflows/local-dev-stack-validate.yml` は次の変更で起動する。

- `firebase.json`
- `.firebaserc`
- `supabase/config.toml`
- `supabase/seed.sql`
- `supabase/migrations/**`
- `scripts/verify_local_dev_stack.py`
- `tests/test_local_dev_stack.py`

CIでは静的検証と `tests/test_local_dev_stack.py` のみを実行する。Dockerイメージ取得を伴う `supabase start` はローカルまたは明示的な統合テストで実施する。

## 禁止事項

- production の `SUPABASE_DB_URL`、`service_role` key、Firebase service account JSON をローカルseedやdocsに貼らない。
- `supabase/seed.sql` に実名、実メール、会社ドメインメール、顧客データを入れない。
- staging / production migration をローカル検証なしで直接適用しない。
- completed WBS の Calendar event を残さない。完了後は通常の WBS closeout sync で削除する。

## トラブル対応

| 症状 | 原因 | 対処 |
| --- | --- | --- |
| `verify_local_dev_stack.py` が `local_env.supabase_db_url` critical を出す | production またはstagingのDB URLが環境変数に残っている | `Remove-Item Env:SUPABASE_DB_URL` 後に再実行する |
| `supabase start` が Docker エラーで止まる | Docker Desktop / 互換ランタイムが起動していない | Dockerを起動し、`docker version` が通ることを確認する |
| seed投入でRLSや外部キーエラーになる | migrationが未適用、またはseedがschemaとずれている | `supabase db reset` で migration + seed を再適用し、seed差分を修正する |
| Firebase Emulator UI が開けない | `firebase.json` の UI port 変更またはポート競合 | `python scripts/verify_local_dev_stack.py --fail-on-critical` を通し、競合プロセスを終了する |

## 完了記録

2026-06-15 に T760 として、設定ファイル、Runbook、検証スクリプト、pytest、GitHub Actions workflow を追加した。後続の T761 / T761_1 では、Supabaseクエリ監視と Firebase/Supabase quota・error alert を本番運用向けに接続する。
