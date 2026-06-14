# パフォーマンス診断・DBインデックス最適化 Runbook (T750)

作成日: 2026-06-14
担当レーン: VSCode + Codex
対象: Firebase Hosting / Firebase Functions / Supabase PostgreSQL

## 目的

本番 API の体感遅延と Supabase PostgreSQL のスロークエリを定期的に検出し、インデックス追加・再構成・不要インデックス削除を安全に判断する。診断は自動化し、DB 変更は承認後に migration として適用する。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- Supabase Managing Indexes: インデックスは検索を高速化する一方で書き込み・容量コストがある。大きいテーブルでは `CREATE INDEX CONCURRENTLY` を使う。
- Supabase Index Advisor / Query Performance: Query Performance 画面から Index Advisor を確認し、推奨インデックスの効果と既存インデックス利用状況を確認する。
- Supabase pg_stat_statements / debugging performance: スロークエリ・実行時間・呼び出し回数を観測する。
- OpenAI Codex / Anthropic Claude Code / Google Gemini: 1 セッション 1 WBS、検証ログを残す、外部ツール変更は権限と証跡を明示する。

## 定期診断

週次 dry-run:

```powershell
python scripts/diagnose_supabase_performance.py --dry-run
python scripts/generate_supabase_query_performance_review.py --fail-on-critical
```

本番 DB 診断:

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:<password>@<host>:6543/postgres?sslmode=require"
python scripts/diagnose_supabase_performance.py --execute --api-url https://mighty-link-ai-connect-13d22.web.app/api/health
python scripts/generate_supabase_query_performance_review.py --fail-on-critical
```

出力:

| 成果物 | 内容 |
| --- | --- |
| `exports/supabase_performance_diagnostic.sql` | 読み取り専用の診断 SQL bundle |
| `exports/supabase_performance_report.json` | 実行計画、プローブ一覧、API応答計測、psqlコマンド（secret redaction済み） |
| `exports/supabase_performance_raw.txt` | `--execute` 時の psql 出力 |
| `exports/supabase_query_performance_review.json` | T761 の機械判定用レビュー結果 |
| `exports/supabase_query_performance_review.md` | Supabase Dashboard / Index Advisor の人間向け確認チェックリスト |

`.github/workflows/supabase-performance-diagnostic.yml` は毎週 dry-run と T761 レビュー生成を実行し、診断 bundle と Dashboard 確認チェックリストが壊れていないことを確認する。実 DB への診断は `SUPABASE_DB_URL` を使うため、手動実行または別途承認された secret 付き workflow で実施する。

## T761 Dashboard Review

T761 では [SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md](SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md) を追加し、診断結果を Supabase Dashboard の Query Performance / Performance Advisor / Index Advisor と照合する手順を標準化した。`scripts/generate_supabase_query_performance_review.py` は T750 の `exports/supabase_performance_report.json` を入力にして、以下を生成する。

- dry-run 診断が揃っているかの自動チェック
- 必須プローブの欠落検知
- Dashboard で確認すべき area / action / decision rule
- `supabase inspect db outliers` などの CLI 裏取りコマンド
- index DDL を直接本番適用しないための migration safety gate

インデックス追加・再構成・削除は T761 で実施しない。Query Performance と `pg_stat_statements` の根拠、Index Advisor の提案、staging での `EXPLAIN (ANALYZE, BUFFERS)`、rollback note が揃った場合に、別 WBS / GitHub Issue として切り出す。

## 診断プローブ

| プローブ | 見るもの | 対応判断 |
| --- | --- | --- |
| `extension_status` | `pg_stat_statements`, `hypopg`, `index_advisor` の有効化状況 | 未有効なら Supabase Dashboard で extension 可否確認 |
| `top_queries_by_total_time` | 総実行時間が大きい SQL | API ルート・画面操作に紐づけて優先度を決める |
| `top_queries_by_mean_time` | 1回あたり遅い SQL | `EXPLAIN (ANALYZE, BUFFERS)` を staging で確認 |
| `sequential_scan_pressure` | Seq Scan が多いテーブル | Index Advisor / 実クエリ条件を照合 |
| `unused_indexes` | 使われていない可能性がある index | 2回以上の診断で継続確認してから削除検討 |
| `large_indexes` | 大きい index | ストレージコストと reindex 候補を確認 |
| `vacuum_analyze_lag` | dead tuples / analyze 遅延 | autovacuum 設定・手動 analyze を検討 |

## インデックス変更の承認フロー

1. `scripts/diagnose_supabase_performance.py --execute` の結果を保存する。
2. Supabase Dashboard の Query Performance と Index Advisor を確認する。
3. 追加候補は staging で `EXPLAIN (ANALYZE, BUFFERS)` を比較する。
4. 本番適用前に GitHub Issue / 課題管理表へ根拠、想定効果、rollback 方法を記録する。
5. `CREATE INDEX CONCURRENTLY` を使う。ただし transaction 内では実行しない。
6. 適用後 24 時間以内に P95 / P99 API 応答、DB CPU、該当 SQL の mean/total time を再測定する。
7. すべての index DDL は `docs/DB_MIGRATION_MANAGEMENT_RUNBOOK.md` に従い、`db/migrations/postgres/` または `supabase/migrations/` の forward migration に残す。

## 再構成・削除の注意

- `REINDEX INDEX CONCURRENTLY <index_name>;` は本番の書き込みブロックを避けるための第一候補。ただし transaction 内では使わない。
- `unused_indexes` に出た index は即削除しない。月次・週次の業務周期で使われる可能性がある。
- Primary key / unique constraint 由来の index は削除対象にしない。
- 小さいテーブルでは Postgres planner が seq scan を選ぶことがあるため、seq scan だけで問題扱いしない。

## APIレスポンス性能

SLA は [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) に従う。

| 指標 | 目標 |
| --- | --- |
| P50 | 1.5 秒以下 |
| P95 | 3.0 秒以下 |
| P99 | 8.0 秒以下 |

週次診断では `/api/health` と主要 API を `--api-url` で計測し、DB 診断結果と合わせてボトルネックを切り分ける。

## 関連ドキュメント

- [SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md](SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md)
- [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md)
- [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md)
- [WBS.md](WBS.md)
