# Firebase / Supabase クォータ・エラー監視アラート Runbook (T761_1)

作成日: 2026-06-15  
担当レーン: VSCode + Codex  
対象: Firebase Hosting / Cloud Functions / Google Cloud Monitoring / Cloud Billing / Supabase Metrics API / Supabase Dashboard

## 目的

T761_1 では、T743 の死活監視、T755 のインフラ横断ダッシュボード、T757 の週次コストダッシュボード、T761 の Supabase Query Performance レビューを束ねて、Firebase と Supabase のクォータ超過・課金急増・エラー増加・DB飽和を人間が見落とさないためのアラート運用を標準化する。

現状の構成は、ドメイン取得はお名前.com、ホスティング/バックエンドは Firebase / GCP、DB は Supabase。現在の本番運用コストはほぼ無料だが、Blaze 化・外部 API 利用・Supabase 有料化・トラフィック増加で費用や quota が変わるため、先に警戒線を決めておく。

## 公式ドキュメント確認メモ

2026-06-15 に以下の公式情報を確認した。

- Firebase は Usage and billing dashboard でプロジェクト利用状況を確認し、予算アラートを作れる。ただし予算アラートは通知であり、利用を自動停止する仕組みではない。
- Firebase Hosting は利用量がプロジェクト単位の quota と料金に影響するため、Usage dashboard と budget alerts で監視する。
- Cloud Functions / Cloud Run のエラーや 5xx は Cloud Logging の logs-based metrics と Cloud Monitoring alert policy に接続できる。
- Firebase Performance Monitoring / alert triggers は、ユーザー影響のある遅延やエラーをイベントとして扱える。
- Supabase Metrics API は Prometheus 互換の database health metrics を提供し、Grafana / Datadog / Cloud Monitoring などへ接続できる。
- Supabase の実利用量・課金・DBサイズ・egress は Dashboard / billing / usage 側を正本にし、レポートへ secret や project ref を保存しない。

## 成果物

| ファイル | 役割 |
| --- | --- |
| `scripts/generate_quota_error_alert_review.py` | 既存監視レポートを横断し、Firebase/Supabase のアラートレビュー JSON/Markdown を生成 |
| `exports/quota_error_alert_review.json` | 機械可読の T761_1 アラートレビュー |
| `exports/quota_error_alert_review.md` | 人間確認用の T761_1 アラートレビュー |
| `.github/workflows/quota-error-alert-review.yml` | 週次/手動/PR でレビューと pytest を実行 |
| `tests/test_quota_error_alert_review.py` | ready/critical/warning 判定、secret redaction、budget 行不足を検証 |

## 実行手順

```powershell
python scripts/check_uptime_targets.py
python scripts/diagnose_supabase_performance.py --dry-run
python scripts/generate_supabase_query_performance_review.py --fail-on-critical
python scripts/rotate_runtime_logs.py --dry-run
python scripts/generate_infra_monitoring_dashboard.py
python scripts/generate_weekly_cost_dashboard.py
python scripts/generate_quota_error_alert_review.py --fail-on-critical
python -m pytest tests/test_quota_error_alert_review.py
```

本番 secret がない環境でも `ready` としてレビューできる。`critical` になるのは、上流の uptime / infra / Supabase query review が本当に危険状態を返した場合。

## アラート設計

| 領域 | 監視信号 | warning | critical | 一次対応 |
| --- | --- | --- | --- | --- |
| Firebase / GCP cost | Cloud Billing, Firebase usage, `firebase_google_cloud` budget | 月次予算 80% | 月次予算 100% または想定外課金 | Cloud Billing budget alert を確認し、T757 へ実績を反映 |
| Firebase Hosting / Functions quota | Hosting transfer/storage, Functions/Cloud Run invocation/memory/timeout | quota 80% または急増 | provider quota 到達、deploy/serve 失敗 | Cloud Monitoring policy 化、必要ならプラン/上限見直し |
| Firebase errors | HTTPS 5xx, Cloud Functions/Run error logs, TLS | 繰り返し error spike | 公開 URL 障害、strict TLS 失敗、5xx 継続 | T743/DR Runbook に従い Issue 起票 |
| Firebase performance | p95 latency, network error, custom trace | SLA に近い遅延 | 主要導線が SLA 逸脱 | Firebase Performance alert trigger を確認 |
| Supabase usage/cost | DB size, egress, storage, MAU, `supabase_db` budget | 月次予算 80% | 月次予算 100% または quota 到達 | Dashboard 正本で確認し、T757 へ実績反映 |
| Supabase health | Metrics API, connections, CPU, memory, disk, WAL, cache hit | 80% resource pressure, p95 query > 1s | blocking locks, disk/WAL危険域, diagnostic failed | T761/T750 に接続し、DDL は別 Issue / migration gate |

## 通知先

- Slack: `SLACK_WEBHOOK_URL` を GitHub Actions secret / CI secret としてのみ保存する。
- Email: `COST_ALERT_EMAIL_TO` や SMTP secret は環境変数だけで渡す。
- GitHub: critical は Issue を起票し、Project #1 と WBS ID を必ず紐付ける。
- Google Workspace: WBS / 課題管理表 / QA表へ反映し、完了済み WBS の Calendar event は削除する。

## Secret 取り扱い

以下は docs、WBS、Sheets、Issues、exports に保存しない。

- `SUPABASE_DB_URL`
- `SUPABASE_METRICS_BEARER_TOKEN`
- `SLACK_WEBHOOK_URL`
- Cloud Billing account ID
- Firebase service account JSON
- Supabase service_role key
- SMTP password

`scripts/generate_quota_error_alert_review.py` は Postgres URL、Bearer token、Slack webhook、Supabase key 風文字列を出力前に redaction する。

## 運用ルール

1. 週次の `Quota Error Alert Review` workflow を確認する。
2. `ready` は「設定候補が明文化済み」、`warning` は「予算行不足や通知先未接続など運用改善対象」、`critical` は「人間対応が必要な障害・quota・DB危険状態」とする。
3. budget alert は自動停止装置ではないため、費用急増時は手動で外部 API / hosting / functions / DB の利用を止める判断をする。
4. Supabase の index 追加、pool size 変更、DB migration は T761/T754 の safety gate を通す。
5. repeated warning は WBS に追加し、GitHub Issue と課題管理表へ接続する。

## 関連ドキュメント

- [UPTIME_MONITORING_AND_ALERT_RUNBOOK.md](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md)
- [INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md](INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md)
- [WEEKLY_COST_DASHBOARD_RUNBOOK.md](WEEKLY_COST_DASHBOARD_RUNBOOK.md)
- [SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md](SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md)
- [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md)
