# スキーマ⇔ドキュメント整合監査 (T880)

- 対象ドキュメント: `docs\database.md`
- 正本テーブル数: **23** / 記載: 23
- 正本ビュー数: **6** / 記載: 6
- 本番適用待ち: kpi_daily_diagnoses, kpi_daily_response_time, kpi_monthly_availability, kpi_weekly_active_users, kpi_weekly_anonymous_sessions, kpi_weekly_diagnosis_accuracy, uptime_checks
- 総合判定: ✅ PASS (ドリフト0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :-- | :-- | :-- | :-- |
| H1 | Supabase本番migration定義の全テーブルがdatabase.mdに記載 | ✅ | 未記載: なし |
| H2 | アプリ実行時legacyテーブル(engineers/jobs/match_results)が記載 | ✅ | 未記載: なし |
| H3 | database.md記載テーブルは全て実スキーマソースに存在(phantom 0) | ✅ | phantom: なし |
| H4 | 6つのSLA KPIビュー(kpi_*)が記載 | ✅ | 未記載ビュー: なし |
| H5 | init_db作成テーブルは全て正規migrationソースにも定義(未管理0) | ✅ | 未管理init_dbテーブル: なし |
| H6 | 旧アーキ(IndexedDB等)のstale記述が除去済み | ✅ | 残存stale語: なし |
| H7 | 正本ソース(supabase/migrations・db/migrations・Runbook)を明示参照 | ✅ | 未参照: なし |
| H8 | 本番未適用(uptime_checks+6ビュー, T778)が『適用待ち』と明記 | ✅ | 未マーク: なし |
| H9 | RLS記述があり、RLS有効化された全テーブルが記載(公式: public全表RLS必須) | ✅ | 未記載RLS表: なし / RLS言及: True |
| H10 | 総テーブル数(23)・ビュー数(6)がdocと算出値で一致し、ドリフト0 | ✅ | doc表数=23/正本=23, docビュー数=6/正本=6, 先行ドリフト=なし |
