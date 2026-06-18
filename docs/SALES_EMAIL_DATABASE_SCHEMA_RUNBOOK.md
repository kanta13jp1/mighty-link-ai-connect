# 営業メールAIマッチング DBスキーマ Runbook

- 作成日: 2026-06-18
- 関連WBS: T817, T817_3
- 関連Issue: #107
- 関連課題: R75, R80
- 対象DB: Supabase/PostgreSQL、ローカルSQLite fallback
- ステータス: T817_3 完了。T817_4のAI抽出deterministic fallback、T817_5の双方向検索API/UIも完了。人間レビューはT817_6以降で実装する。

---

## 目的

営業メールAIマッチング機能で、共有営業アドレスに届く案件メール、要員メール、スキル要件メールを安全にDB化するための初期スキーマ、RLS、migration、seed、rollbackを管理する。

今回のT817_3では、本文全文やOAuthトークンを保存せず、hash、redacted excerpt、構造化された案件/要員/スキル情報、解析ログ、マッチング結果、レビュー結果を保存できる土台までを整備した。実メールのGmail接続やAI抽出結果の確定ロジックはまだ含めない。

## 正本ファイル

| 用途 | ファイル |
| --- | --- |
| Supabase migration | `supabase/migrations/20260618000000_sales_email_matching_schema.sql` |
| PostgreSQL runtime migration | `db/migrations/postgres/20260618000000_sales_email_matching_schema.sql` |
| SQLite fallback migration | `db/migrations/sqlite/20260618000000_sales_email_matching_schema.sql` |
| rollback SQL | `db/migrations/rollback/20260618000000_sales_email_matching_schema_rollback.sql` |
| synthetic seed | `supabase/seed.sql` |
| 検証テスト | `tests/test_sales_email_schema_migrations.py` |

## 追加テーブル

| テーブル | 役割 |
| --- | --- |
| `sales_mailbox_sources` | Gmail、手動アップロード、CSVなどの取り込み元 |
| `sales_email_messages` | メールメタ情報、dedupe key、送信者hash、本文hash、redacted excerpt |
| `sales_email_entities` | メールから抽出した案件、要員、会社、スキル、条件 |
| `project_requirements` | 案件要件、必須/尚可スキル、単価、勤務地、商流、根拠 |
| `talent_profiles_from_email` | メール由来の要員情報、スキル、稼働条件、匿名化キー |
| `requirement_skill_tags` | 案件/要員に紐づくスキルタグと重要度 |
| `email_parse_runs` | 取り込み/抽出実行ログ、件数、モデル名、fallback有無 |
| `email_match_results` | 案件と要員/エンジニアのマッチ結果、スコア、根拠、不一致理由 |
| `email_match_feedback` | 人間レビュー、採用/却下、補正スコア、補足メモ |

## セキュリティ方針

1. メール本文全文、OAuthトークン、service role secret、添付ファイル実体は保存しない。
2. `sales_email_messages.raw_storage_policy` は `hash_and_redacted_excerpt_only` に固定する。
3. Supabase側は全テーブルでRLSを有効化し、`anon` と `authenticated` からの直接アクセスを `REVOKE ALL` する。
4. T817_5の候補検索APIはsanitized extraction reviewを読むだけで、Supabaseへ匿名REST直書きしない。公開RESTからの読み書き用 `CREATE POLICY` は、人間レビュー保存と実メールDB運用を扱うT817_6以降で必要最小限に追加する。
5. 本番適用時は、Supabase Dashboardまたはバックアップスクリプトでbackup/PITR時刻を記録してから1レーンだけが実行する。
6. GitHub Issue、Sheets、NotebookLM、公開資料には実メール本文、個人メールアドレス、電話番号、認証情報を記録しない。

## 検証コマンド

```powershell
python scripts/manage_db_migrations.py validate --engine sqlite
python scripts/manage_db_migrations.py validate --engine postgres
python scripts/manage_db_migrations.py validate --engine supabase
python -m pytest tests/test_sales_email_schema_migrations.py tests/test_db_migration_management.py tests/test_rls_policies.py -q
```

SQLite fallbackへ実適用する場合は、一時DBまたは開発用DBで確認する。

```powershell
python scripts/manage_db_migrations.py apply --engine sqlite --sqlite-path data/mighty.db --dry-run
```

`--dry-run` でpending/applied/checksumを確認し、必要な場合だけ `--dry-run` を外す。

## Supabase適用手順

1. `git pull --ff-only origin main` で最新化する。
2. 他レーンへDB migration適用中でないことを確認する。
3. Supabase Dashboardまたは `scripts/backup_supabase_database.py` でbackup/PITR時刻を記録する。
4. `supabase migration list --linked` で履歴差分を確認する。
5. stagingで `supabase db reset` または `supabase db push` を検証する。
6. 本番で `supabase db push` を実行する。
7. RLS/RESTアクセス、API smoke test、公開デモguard、WBS/Sheets/Calendar/GitHub同期を実施する。

## rollback方針

`db/migrations/rollback/20260618000000_sales_email_matching_schema_rollback.sql` は、開発・staging検証と緊急時の参照用である。本番で実行する場合は、次の条件を満たす。

1. 書き込み停止またはメンテナンス告知を行う。
2. backup/PITR時刻、対象Issue、判断者を記録する。
3. 影響範囲を確認し、可能ならforward-fix migrationを優先する。
4. 破壊的DROPが必要な場合は、復元先DBでリハーサルしてから実行する。

## 次工程

- T817_4: 完了。Gmail/ファイル取り込み結果から案件要件、要員情報、スキルタグを抽出し、根拠抜粋と信頼度を保存できる構造を `docs/SALES_EMAIL_EXTRACTION_PIPELINE_RUNBOOK.md` に整理済み。
- T817_5: 完了。双方向検索API/UIを作り、案件から候補人材、人材から候補案件を表示する。
- T817_6: 人間レビュー、採用/却下、補正ログ、フィードバック改善ループを実装する。
- T817_7: 個人情報最小化、監査ログ、保持/削除、負荷、アカウント移管、Go/No-Goを確認する。

## 公式ドキュメント確認メモ

- Supabase Database Migrations: https://supabase.com/docs/guides/deployment/database-migrations
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Gmail API Guides: https://developers.google.com/workspace/gmail/api/guides
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
