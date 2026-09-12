# インフラ・テレメトリ監視ダッシュボード Runbook (T755)

作成日: 2026-06-14
担当レーン: Codex
対象: Firebase Hosting / Cloud Run Functions / Supabase / GitHub Actions / ローカルCI成果物

## 目的

死活監視、DB性能診断、ログ保持、外部API利用状況を横断して、CPU・メモリ・ディスク・クエリ・URL到達性を一枚のダッシュボードで確認できる状態にする。T743/T748/T750/T753/T754の個別運用を束ね、T757のコスト監視やT761_1のクォータ/エラー監視へ接続する。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- Supabase Metrics API: Prometheus互換 endpoint で Postgres のCPU、IO、WAL、connection、query metrics を取得できる。
- Supabase Logging / Inspect: Logs Explorer と SQL 診断で query performance、locks、index、disk を確認する。
- Firebase Performance Monitoring / Google Cloud Monitoring: client/server metrics と Cloud Functions / Cloud Run のCPU・メモリ・レイテンシを監視する。
- Amazon Bedrock / Microsoft Foundry / BytePlus ModelArk: AI利用量、latency、error、token metrics を provider dashboard で継続監視する。
- GitHub Actions: workflow は `.github/workflows` に配置し、schedule / workflow_dispatch / paths で運用単位を分ける。
- Slack / Discord / Stripe: webhook 通知はsecretとして扱い、ログ・report・Issueへ値を出さない。

## 成果物

| ファイル | 役割 |
| --- | --- |
| `scripts/generate_infra_monitoring_dashboard.py` | 既存レポートとローカルリソースを集約してJSON/Markdownを生成 |
| `exports/infra_monitoring_dashboard.json` | 機械可読の直近ダッシュボード |
| `exports/infra_monitoring_dashboard.md` | 人間向けのテーブル表示 |
| `.github/workflows/infra-telemetry-dashboard.yml` | 日次/手動でダッシュボード生成を検証 |
| `tests/test_infra_monitoring_dashboard.py` | secret redaction、Prometheus parsing、集約ロジックのテスト |

## 手動実行

```powershell
python scripts/check_uptime_targets.py
python scripts/diagnose_supabase_performance.py --dry-run
python scripts/rotate_runtime_logs.py --dry-run
python scripts/generate_infra_monitoring_dashboard.py
```

criticalをCI失敗扱いにする場合:

```powershell
python scripts/generate_infra_monitoring_dashboard.py --fail-on-critical
```

ローカルPC/CIランナーのhost resourceは本番障害ではないため、既定ではディスク90%以上、メモリ95%以上、load/core 1.0以上もwarningに丸める。host resourceもcriticalとして扱いたい場合:

```powershell
$env:INFRA_HOST_RESOURCE_CRITICAL = "1"
python scripts/generate_infra_monitoring_dashboard.py --fail-on-critical
```

## Supabase Metrics API 接続

GitHub Actions またはローカルで以下を設定すると Prometheus互換metricsを取り込める。

```powershell
$env:SUPABASE_METRICS_URL = "https://..."
$env:SUPABASE_METRICS_BEARER_TOKEN = "..."
python scripts/generate_infra_monitoring_dashboard.py
```

reportにはmetric名とカテゴリだけを保存し、Bearer token やDB接続文字列は保存しない。長期保管やアラートは Grafana / Datadog / Sentry / Google Cloud Monitoring へ接続する。

## 判定

| カテゴリ | 主な入力 | warning | critical |
| --- | --- | --- | --- |
| host | disk / memory / CPU / repo artifact size | ディスク80%以上、メモリ85%以上、load/core 0.75以上。既定ではlocal/CI runnerのcritical相当値もwarningに丸める | `INFRA_HOST_RESOURCE_CRITICAL=1` の場合のみディスク90%以上、メモリ95%以上、load/core 1.0以上 |
| availability | `exports/uptime_monitor_report.json` | TLS pendingなどwarningあり | 監視対象failedあり |
| database | Supabase diagnostic / Metrics API | dry-runのみ、Metrics API未設定 | diagnostic failed、report破損 |
| logs | log rotation report | rotation候補あり | report破損 |
| cost | external API usage ledger | billable eventあり | provider側の実請求異常はT757へ起票 |

## 運用ルール

1. 日次で `Infra Telemetry Dashboard` workflow を確認する。
2. warningは通常の改善候補としてWBS/Issueへ接続する。
3. availability/database/logsのcriticalは障害扱いで [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) を参照する。host resource warningは実行端末の状態として扱い、本番判断はCloud Monitoring/Supabase Metricsで行う。
4. Supabase Metrics APIが利用可能になったら、T761_1でアラート閾値をGoogle Cloud MonitoringまたはGrafanaへ移す。
5. Provider dashboardの実請求・quotaはT757/T761_1の正本にし、本ダッシュボードは横断ビューとして使う。

## 関連ドキュメント

- [UPTIME_MONITORING_AND_ALERT_RUNBOOK.md](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md)
- [PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md](PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md)
- [LOG_ROTATION_AND_RETENTION_RUNBOOK.md](LOG_ROTATION_AND_RETENTION_RUNBOOK.md)
- [API_RATE_LIMIT_AND_DDOS_RUNBOOK.md](API_RATE_LIMIT_AND_DDOS_RUNBOOK.md)
- [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md)
