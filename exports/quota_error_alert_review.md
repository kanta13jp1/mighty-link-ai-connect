# Firebase and Supabase Quota/Error Alert Review

- Task: T761_1
- Generated: 2026-06-14T19:09:19Z
- Overall status: ready

## Summary

| Status | Count |
| --- | ---: |
| ok | 1 |
| ready | 8 |
| warning | 0 |
| critical | 0 |

## Alert Checks

| Key | Provider | Status | Signal | Threshold | Action | Notification | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| firebase_billing_budget_alert | Firebase / Google Cloud | ready | Cloud Billing actual spend, Firebase plan usage, Hosting/Functions cost center | Warning at 80% and critical at 100% of firebase_google_cloud monthly budget | Create or verify a Cloud Billing budget alert and keep billed actuals in the weekly cost dashboard. | Budget email notification plus optional Slack relay through existing cost alert draft | firebase_google_cloud monthly_budget_usd=10.00, warning_ratio=0.80, critical_ratio=1.00; cost_report=ready |
| firebase_hosting_functions_quota | Firebase / Google Cloud | ready | Firebase Hosting transfer/storage, Functions/Cloud Run invocations, memory, timeout, and quota usage | Warning when dashboard usage exceeds 80%; critical when provider quota or deployment limit is reached | Review Firebase Usage and Cloud Run/Functions quotas weekly; convert repeated warnings to Cloud Monitoring policies. | Ops Slack/Email after manual threshold confirmation; no provider token is stored in artifacts | infra_report=warning |
| firebase_error_log_alert | Firebase / Google Cloud | ready | HTTPS uptime failures, 5xx responses, Cloud Functions/Cloud Run error logs, TLS certificate failures | Critical on public demo outage, custom domain strict TLS failure, or repeated 5xx/log-based error spikes | Create a Cloud Logging logs-based metric and Cloud Monitoring alert policy for 5xx and function error logs. | Slack webhook or email notification, then follow DR and incident postmortem runbooks | uptime_report=ready; infra_report=warning |
| firebase_performance_alert | Firebase | ready | Firebase Performance Monitoring latency, network errors, and custom trace degradation | Warning on sustained p95 latency regression; critical when user-visible flows breach SLA thresholds | Define Performance Monitoring alert events for key user journeys after live traffic exists. | Firebase alert trigger to Cloud Functions or operator email, then GitHub Issue for recurring degradation | No production traffic baseline yet; keep as ready gate until enough samples exist |
| supabase_usage_budget_alert | Supabase | ready | Supabase spend, egress, database size, storage, auth MAU, and plan usage | Warning at 80% and critical at 100% of supabase_db monthly budget or provider quota | Check Supabase billing/usage dashboard weekly and record actuals without project IDs or secrets. | Weekly cost dashboard alert draft plus operator escalation for paid-plan changes | supabase_db monthly_budget_usd=25.00, warning_ratio=0.80, critical_ratio=1.00 |
| supabase_metrics_api_alert | Supabase | ready | Prometheus-compatible database health metrics from Supabase Metrics API | Warning on missing scrape; critical on connection saturation, disk pressure, WAL backlog, or error burst | Add SUPABASE_METRICS_URL and SUPABASE_METRICS_BEARER_TOKEN as CI/environment secrets before live alerting. | Grafana/Datadog/Cloud Monitoring bridge or GitHub Actions summary; token values never enter reports | metrics endpoint not configured in this environment |
| supabase_db_saturation_alert | Supabase | ready | Slow query review, connection pressure, CPU, memory, disk, locks, WAL, cache hit rate, and index advisor findings | Warning at 80% resource pressure or repeated p95 query latency > 1s; critical on blocking locks or failed diagnostics | Use Query Performance / Performance Advisor / Index Advisor review before opening DDL or pool-size changes. | GitHub Issue plus WBS follow-up; production DDL requires migration safety gate | query_review=ready |
| notification_channel_routing | Operations | ready | Slack webhook, email destination, GitHub Actions failure, and Issue/Project escalation | Critical alerts must reach a human-owned channel; warning alerts may stay in scheduled report artifacts | Store SLACK_WEBHOOK_URL and email settings only as GitHub/CI secrets; never write them to docs, Sheets, or Issues. | Slack, email, GitHub Issue comment, and Calendar/WBS closeout | notification secrets not configured locally; CI can inject them |
| incident_escalation_gate | Operations | ok | Critical alert handoff, DR escalation, postmortem creation, and WBS follow-up | Any critical production availability/data-loss/billing runaway alert starts incident handling | Open/close GitHub Issue with WBS reference and attach follow-up actions to issues_tracker.tsv and qa_tracker.tsv. | Human operator, GitHub Issue #97, Project #1, and Google Workspace WBS sync | runbooks present |

## Operator Checklist

| Area | Action | Evidence |
| --- | --- | --- |
| Cloud Billing | Verify Firebase/GCP budget alert recipients and thresholds before enabling paid expansion. | Weekly cost dashboard row for firebase_google_cloud plus Cloud Billing budget policy screenshot/export. |
| Cloud Monitoring | Create alert policies for HTTPS 5xx/log-based errors, Functions/Cloud Run errors, and TLS failures. | Alert policy name, notification channel, and GitHub Issue link. |
| Firebase | Review Hosting/Functions usage and Performance Monitoring alert events after production traffic starts. | Firebase usage dashboard and Performance Monitoring alert settings. |
| Supabase | Enable Metrics API/Grafana-style scraping and watch connection, CPU, disk, WAL, cache, and slow query signals. | Metrics scrape status plus Supabase Query Performance review artifact. |
| Escalation | Route critical alerts to a human-owned channel and open a WBS-linked Issue for follow-up. | Issue/Project status, Sheets sync, and Calendar cleanup for completed WBS rows. |

## Escalation Rules

- Do not store Slack webhooks, Supabase bearer tokens, database URLs, or billing account identifiers in artifacts.
- Treat Cloud Billing budget alerts as notifications, not automatic spend caps.
- Convert repeated warning alerts into WBS tasks with GitHub Issues and Project status.
- Escalate critical availability, quota exhaustion, or data-loss risk through the DR and incident runbooks.
