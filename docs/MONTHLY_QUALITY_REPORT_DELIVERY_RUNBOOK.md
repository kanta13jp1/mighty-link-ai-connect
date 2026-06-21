# 月次品質レポート自動配信 Runbook (T808)

T764 の `docs/MONTHLY_REPORT_YYYY-MM.md` を、T767 の月次KPIダッシュボード仕様に従って Google Sheets、Notion、Slack へ配信する。

## 対象

| 配信先 | 実装 | 既定動作 |
| :--- | :--- | :--- |
| Google Sheets | `scripts/sync_monthly_kpi_to_sheets.py` | `月次KPIサマリー` タブへ月単位でupsert |
| Notion | `scripts/post_report_to_notion.py` | payload/status JSONを作成し、認証情報があればページ作成 |
| Slack | `scripts/send_monthly_slack_report.py` | payload/status JSONを作成し、`SLACK_WEBHOOK_URL` があれば送信 |
| GitHub Actions | `.github/workflows/monthly-quality-report-delivery.yml` | 毎月1日 09:00 JST に前月分を配信 |

## 手動実行

```powershell
python scripts/generate_monthly_quality_report.py --month 2026-06 --today 2026-07-01
python scripts/sync_monthly_kpi_to_sheets.py --month 2026-06 --today 2026-07-01
python scripts/post_report_to_notion.py --month 2026-06 --today 2026-07-01
python scripts/send_monthly_slack_report.py --month 2026-06 --today 2026-07-01
```

Google Sheets だけを必ず同期したい場合:

```powershell
python scripts/sync_monthly_kpi_to_sheets.py --month 2026-06 --today 2026-07-01 --require-sync
```

## GitHub Actions secrets / vars

| 名前 | 用途 | 備考 |
| :--- | :--- | :--- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Sheets同期 | JSON本文をsecretへ保存。成果物には書かない |
| `NOTION_API_KEY` または `NOTION_TOKEN` | Notion API | Integration token |
| `NOTION_MONTHLY_REPORT_DATABASE_ID` | Notion DB投稿 | database parentを使う場合 |
| `NOTION_MONTHLY_REPORT_DATA_SOURCE_ID` | Notion data source投稿 | data source parentを使う場合 |
| `NOTION_MONTHLY_REPORT_PARENT_PAGE_ID` | Notion page配下投稿 | page parentを使う場合 |
| `SLACK_WEBHOOK_URL` | Slack通知 | webhook URLはsecretのみ |
| `NOTION_MONTHLY_REPORT_TITLE_PROPERTY` | Notionタイトル列名 | GitHub variable。未設定なら `Name` |

Notion は `NOTION_DATABASE_ID` / `NOTION_DATA_SOURCE_ID` / `NOTION_PARENT_PAGE_ID` のいずれかが必要。ローカル手動実行では同名の環境変数も利用できる。

## 成果物

| ファイル | 内容 |
| :--- | :--- |
| `exports/monthly_quality_kpi_YYYY-MM.json` | Sheetsへ同期するKPI summary |
| `exports/monthly_quality_notion_payload_YYYY-MM.json` | Notion create page payload |
| `exports/monthly_quality_notion_status_YYYY-MM.json` | Notion投稿結果またはskip理由 |
| `exports/monthly_quality_slack_payload_YYYY-MM.json` | Slack payload |
| `exports/monthly_quality_slack_status_YYYY-MM.json` | Slack送信結果またはskip理由 |

これらの成果物には webhook URL、Notion token、Google OAuth token、service account JSON を保存しない。

## 未計測KPIの扱い

2026-06時点では、SLA稼働率、P95レスポンス、5xxエラー率、Firebase費用、Supabase費用の live source は未接続のため、`未計測` としてSheetsに保持する。T800/T807/T811で実データ連携が完了したら同じ月行をupsertし、値だけを更新する。

パイロット実績から取得できる値は以下を使う。

- `data/pilot_summary.tsv` の「テストマッチング回数」→ 診断件数
- `data/pilot_summary.tsv` の「診断結果の適合精度」→ 精度スコア
- `data/pilot_summary.tsv` の「期間中累積APIコスト」→ Gemini費用の暫定実績

## 失敗時対応

| 症状 | 対応 |
| :--- | :--- |
| Sheetsが `skipped_missing_credentials` | `GOOGLE_SERVICE_ACCOUNT_JSON`、またはローカル `client_secret.json` + `authorized_user.json` を確認 |
| Notionが `skipped_missing_credentials` | token と parent ID の両方を確認 |
| Slackが `skipped_missing_credentials` | `SLACK_WEBHOOK_URL` secret を確認 |
| HTTP 429 | スクリプトはNotion 429のみ1回短時間retryする。継続する場合は翌実行へ回し、手動再実行 |
| 送信payloadにsecretが混入しそう | `tests/test_monthly_quality_delivery.py` を実行し、secret非混入テストを確認 |

## 検証

```powershell
python -m pytest tests/test_monthly_quality_delivery.py tests/test_monthly_quality_report.py
```

Closeoutでは通常のWBS同期と合わせて以下も確認する。

```powershell
python scripts/verify_google_workspace_account.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```
