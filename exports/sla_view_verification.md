# SLA計測ビュー オフライン検証ログ (T778_1)

- レポートID: `SLA_VIEW_VERIFICATION_T778_1`
- 実施日: 2026-07-08
- 判定: **ok** (10/10 仮説PASS)
- スコープ: オフラインのビュー/レポート検証。本番Supabaseへのmigration適用と実データでのビュー検証はSUPABASE_DB_URL必須の人間工程（T778本体）。

## 10仮説検証

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | ビュー kpi_daily_diagnoses が参照する列がスキーマに存在する | PASS | matches(created_at/user_id/fit_score) → 全列存在 |
| H2 | ビュー kpi_weekly_active_users が参照する列がスキーマに存在する | PASS | matches(created_at/user_id) → 全列存在 |
| H3 | ビュー kpi_weekly_anonymous_sessions が参照する列がスキーマに存在する | PASS | usage_analytics_events(created_at/session_pseudonym) → 全列存在 |
| H4 | ビュー kpi_monthly_availability が参照する列がスキーマに存在する | PASS | uptime_checks(checked_at/target_id/status) → 全列存在 |
| H5 | ビュー kpi_daily_response_time が参照する列がスキーマに存在する | PASS | uptime_checks(checked_at/target_id/response_ms) → 全列存在 |
| H6 | ビュー kpi_weekly_diagnosis_accuracy が参照する列がスキーマに存在する | PASS | feedback_events(created_at/rating) → 全列存在 |
| H7 | evaluate(): 全指標が目標達成のときPASS判定になる | PASS | availability=True p95=True helpful=True |
| H8 | evaluate(): 目標未達（可用性/遅延/精度）を全てFAILとして検出する | PASS | FAIL検出=['availability_pct', 'helpful_pct', 'p95_ms']（3指標全てFAIL期待） |
| H9 | evaluate(): データ無しでも例外にならずNO-DATAを返す | PASS | NO-DATA件数=3/3 |
| H10 | レポート生成は認証情報無しで安全に停止し、目標値がpilot SLA定義と一致する | PASS | SUPABASE_DB_URL無しの戻り値=1(1期待) targets={'availability_pct_pilot': 99.5, 'p95_ms': 3000, 'helpful_pct': 70.0} |

## 残作業（T778本体・人間/認証情報依存）

- 本番Supabaseへの `supabase/migrations/20260705000000_sla_measurement_views.sql` 適用（`SUPABASE_DB_URL` 必須の運用者工程）。
- 実データでの `python scripts/generate_sla_measurement_report.py` 実行とSLA/KPIレポートのSheets同期（T764/T808パイプライン）。
- `scripts/check_uptime_targets.py --record-db` による稼働サンプルの継続蓄積。
