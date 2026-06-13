# Infra Telemetry Dashboard

- Task: T755
- Generated: 2026-06-13T21:45:32Z
- Overall status: warning

## Summary

| Status | Count |
| --- | ---: |
| ok | 3 |
| unknown | 1 |
| warning | 6 |
| critical | 0 |

## Checks

| Category | Key | Status | Value | Recommendation |
| --- | --- | --- | --- | --- |
| host | disk_usage | warning | 86.98% used (60720.0 MB free / 466325.0 MB total) | Investigate generated artifacts, logs, and old archives if disk usage exceeds 80%; set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation. |
| host | memory_usage | warning | 93.00% used (1035.9 MB available / 16068.7 MB total) | Use Google Cloud Monitoring / Cloud Run metrics for production memory saturation; set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation. |
| host | cpu_load | unknown | load average unavailable; cpu_count=20 | Use Cloud Monitoring CPU utilization and Cloud Run concurrency for production CPU alerting; set INFRA_HOST_RESOURCE_CRITICAL=1 to fail local/CI runner saturation. |
| host | repo_data_exports_size | ok | data=0.6 MB, exports=71.7 MB | Keep generated artifacts bounded; large binary growth should move to Drive/GCS. |
| availability | uptime_summary | warning | ok=2 warning=1 failed=0 | Investigate failed targets; TLS warnings for mightylink-app.com remain expected until T740_3. |
| availability | uptime_max_latency | ok | 74.55 ms | Correlate high latency with Firebase Hosting and Cloud Run metrics. |
| database | db_query_diagnostics | warning | status=planned, dry_run=True, probes=7 | Use --execute with SUPABASE_DB_URL for live query telemetry before production DB changes. |
| logs | log_rotation_backlog | warning | rotation_candidates=1, prune_candidates=0 | Run real log rotation if candidates remain after review. |
| cost | external_api_usage | ok | events=50, billable=0, blocked=50 | Compare billable usage with T757 cost dashboard and provider consoles. |
| database | supabase_metrics_api | warning | not configured | Set SUPABASE_METRICS_URL and token secret in CI to scrape Prometheus-compatible Supabase metrics. |

## Sources

- uptime: `exports\uptime_monitor_report.json`
- database_performance: `exports\supabase_performance_report.json`
- log_rotation: `exports\log_rotation_report.json`
- external_api_usage: `data\external_api_usage.jsonl`
- supabase_metrics_api: `not configured`

## Notes

- This artifact contains no secret values. Runtime secrets are read only to connect to optional APIs.
- Supabase Metrics API scraping is optional until the project token and endpoint are configured in GitHub secrets.
- Custom domain TLS warning remains expected until T740_3 is complete.
