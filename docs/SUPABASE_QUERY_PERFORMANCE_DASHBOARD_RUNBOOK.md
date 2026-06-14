# Supabase クエリ性能ダッシュボード運用 Runbook (T761)

作成日: 2026-06-15  
担当レーン: VSCode + Codex  
対象: Supabase PostgreSQL / Firebase Functions / 本番 API

## 目的

Supabase Dashboard の Query Performance、Performance Advisor、Index Advisor と、`scripts/diagnose_supabase_performance.py` の診断結果を突き合わせ、スロークエリとインデックス変更の判断を証跡化する。T761 は「すぐに index DDL を適用する」タスクではなく、運用者が安全に判断できるレビュー成果物と週次ゲートを整えるタスクである。

## 公式ドキュメント確認

2026-06-15 に以下を確認した。

- Supabase Performance Tuning / Query Optimization: Query Performance と `EXPLAIN` を使い、実クエリ・実データ量に基づいて最適化する。
- Supabase Performance and Security Advisors: Advisor の警告は定期確認し、影響範囲と修正方針を記録する。
- Supabase index_advisor / Managing Indexes: 推奨 index は既存 index と query plan を比較し、書き込みコストも含めて判断する。
- Supabase pg_stat_statements / Debugging and monitoring: `pg_stat_statements` と `supabase inspect db` を併用し、total time、mean time、seq scan、unused index を確認する。
- GitHub Actions / Google Sheets batchUpdate: dry-run 成果物は CI で壊れないことを確認し、WBS・課題・QA は Sheets へ一括同期する。

## 週次レビュー手順

1. 診断 SQL と dry-run レポートを生成する。

```powershell
python scripts/diagnose_supabase_performance.py --dry-run
```

2. T761 レビュー成果物を生成する。

```powershell
python scripts/generate_supabase_query_performance_review.py --fail-on-critical
```

3. `exports/supabase_query_performance_review.md` を開き、Dashboard Checklist の各行を確認する。

4. Supabase Dashboard で以下を確認する。

| 画面 | 確認内容 | 判定 |
| --- | --- | --- |
| Database > Query Performance | total time / mean time / calls の上位SQL | APIルートまたはUI操作へ紐づけできるか |
| Database > Performance Advisor | 本番影響のある警告 | GitHub Issue と課題管理表に記録するか |
| Database > Index Advisor | 推奨 index と既存 index | `EXPLAIN` と業務クエリ形状で根拠があるか |
| SQL Editor / CLI | `supabase inspect db ...` | Dashboard 所見と矛盾しないか |

5. 変更候補がある場合は、T761 で直接DDLを適用せず、別Issue/WBSへ切り出す。

## 本番DBを使う診断

本番実行は承認済みのメンテナンス枠でのみ行う。`SUPABASE_DB_URL` は環境変数だけで渡し、docs、Sheets、Issue、ログへ値を残さない。

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:<password>@<pooler-host>:6543/postgres?sslmode=require"
python scripts/diagnose_supabase_performance.py --execute --api-url https://mightylink-app.com/api/health
python scripts/generate_supabase_query_performance_review.py --fail-on-critical
```

成果物:

| ファイル | 内容 |
| --- | --- |
| `exports/supabase_performance_report.json` | T750 診断レポート。secret-like値はredact済み |
| `exports/supabase_query_performance_review.json` | T761 レビュー判定。CIやSheets連携の入力 |
| `exports/supabase_query_performance_review.md` | 人間が読む Dashboard review checklist |

## `supabase inspect db` コマンド

Dashboard 所見の裏取りとして、以下を使用する。

```powershell
supabase inspect db outliers
supabase inspect db index-usage
supabase inspect db unused-indexes
supabase inspect db seq-scans
supabase inspect db cache-hit
supabase inspect db locks
supabase inspect db blocking
```

CLI が使えない場合は Dashboard と T750 SQL bundle のみでレビューし、CLI未実行を Issue の前提条件に明記する。

## インデックス変更の受け入れ条件

- 同じSQLまたは同じ業務操作で、Query Performance と `pg_stat_statements` の両方に遅延根拠がある。
- Index Advisor の提案が既存 index と重複していない。
- staging または production-like data で `EXPLAIN (ANALYZE, BUFFERS)` を比較済み。
- 書き込み頻度、容量、maintenance cost を確認済み。
- GitHub Issue、課題管理表、WBS、rollback note が揃っている。
- 本番級テーブルでは `CREATE INDEX CONCURRENTLY` を優先し、transaction 内では実行しない。

## 完了条件

T761 は以下を満たした時点で完了とする。

- `scripts/generate_supabase_query_performance_review.py` が T750 診断レポートからレビュー成果物を生成する。
- CI が dry-run 診断と T761 レビュー生成を実行する。
- `exports/supabase_query_performance_review.md` に Supabase Dashboard の確認観点が残る。
- WBS、課題管理表、QA表、GitHub Issue / Project、Calendar が同期される。

## 関連ドキュメント

- [PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md](PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md)
- [SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md](SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md)
- [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md)
- [SUPABASE_CONNECTION_POOLING_RUNBOOK.md](SUPABASE_CONNECTION_POOLING_RUNBOOK.md)
- [INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md](INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md)
- [WBS.md](WBS.md)
