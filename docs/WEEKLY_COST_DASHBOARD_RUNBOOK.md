# 週次課金・コスト配分ダッシュボード Runbook (T757)

作成日: 2026-06-14
担当レーン: VSCode + Codex
対象: Google Cloud / Firebase / Supabase / Stripe / GitHub Actions / Slack通知 / 外部AI API利用台帳

## 目的

T757では、日次のAPI利用監査(T736)とインフラ横断監視(T755)の上に、週次のコスト配賦ビューと通知ドラフトを追加する。実請求額の正本は各プロバイダーの請求/使用量画面に置き、リポジトリ側では「どのコストセンターが、どのレーンに属し、どの予算閾値に近いか」を同じフォーマットで確認できるようにする。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- Google Cloud Billing: Cloud Billing export to BigQuery は usage/cost/pricing データをBigQueryへ自動出力し、詳細分析に使える。
- Firebase Billing: Firebase project全体でSpark/Blazeの料金プランが適用され、Budgets & Alerts から予算アラートを作成できる。
- Stripe Billing Meters: Meter eventsは顧客の利用アクションを課金メーターへ集計し、meter event summaryはページングして取得する。
- Supabase: Management APIはrate limit headerを返し、使用量/egress/DB sizeはDashboardやReportsで確認する。
- Slack: incoming webhook / chat.postMessage は概ね1秒1メッセージ/チャンネルの制限を意識し、webhook URLはsecretとして扱う。
- GitHub Actions: workflowは `.github/workflows` に置き、schedule / workflow_dispatch / pull_request pathsで運用単位を分ける。

## 成果物

| ファイル | 役割 |
| --- | --- |
| `data/cost_allocation_budgets.tsv` | コストセンター、担当レーン、月次予算、閾値、請求正本の一覧 |
| `scripts/generate_weekly_cost_dashboard.py` | 週次コスト配賦JSON/Markdownと通知ドラフトを生成 |
| `exports/weekly_cost_dashboard.json` | 機械可読の週次ダッシュボード |
| `exports/weekly_cost_dashboard.md` | 人間向けの週次ダッシュボード |
| `exports/weekly_cost_alert_email.md` | メール送信用ドラフト本文 |
| `exports/weekly_cost_slack_payload.json` | Slack送信用payloadドラフト |
| `.github/workflows/weekly-cost-dashboard.yml` | 週次/手動/PRで生成とテストを検証 |
| `tests/test_weekly_cost_dashboard.py` | 配賦、budget判定、secret非出力、alert終了コードのテスト |

## 手動実行

```powershell
python scripts/audit_external_api_usage.py --write-default-report
python scripts/generate_weekly_cost_dashboard.py
python -m pytest tests/test_weekly_cost_dashboard.py
```

warning/criticalをCI失敗扱いにする場合:

```powershell
python scripts/generate_weekly_cost_dashboard.py --fail-on-alert
```

## 実請求データの接続

実請求額をリポジトリへ反映する場合は、秘密値を含まないTSVを `data/cost_actuals.tsv` として作成する。

```tsv
period_start	period_end	cost_center	amount_usd	source	notes
2026-06-08	2026-06-14	firebase_google_cloud	0.00	Cloud Billing export	manual export without billing account id
```

`source` にはプロバイダー名やexport種別だけを書き、請求アカウントID、API key、webhook URL、顧客ID、カード情報は書かない。

## 通知

既定では送信せず、以下を生成する。

- `exports/weekly_cost_alert_email.md`
- `exports/weekly_cost_slack_payload.json`

実送信する場合:

```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
python scripts/generate_weekly_cost_dashboard.py --send-slack
```

```powershell
$env:SMTP_HOST = "smtp.example.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "..."
$env:SMTP_PASSWORD = "..."
python scripts/generate_weekly_cost_dashboard.py --send-email --email-to "ops@example.com" --email-from "noreply@example.com"
```

Slack webhook URL、SMTP password、API keyは成果物に保存しない。

## 判定

| 状態 | 条件 | 対応 |
| --- | --- | --- |
| ok | 実請求が予算warning未満、または外部APIが全てblocked/無料 | 通常運用 |
| unknown | 実請求export未接続でbillable eventなし | プロバイダー正本の確認を継続 |
| warning | 実請求がwarning閾値以上、billable eventの実請求未接続、JSONL破損 | R11/R35または該当WBSへ接続 |
| critical | 実請求がcritical閾値以上 | 人間承認まで新規外部課金呼び出しを止める |

## 関連ドキュメント

- [AI_COST_MONITORING_AND_QUOTA_DESIGN.md](AI_COST_MONITORING_AND_QUOTA_DESIGN.md)
- [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md)
- [INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md](INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md)
- [API_RATE_LIMIT_AND_DDOS_RUNBOOK.md](API_RATE_LIMIT_AND_DDOS_RUNBOOK.md)
- [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md)
