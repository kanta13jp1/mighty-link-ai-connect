# Support Contact and Escalation Runbook (T790)

作成日: 2026-06-16  
対象: 問い合わせフォーム / 暫定メール窓口 / 一次回答SLA / エスカレーション

## 目的

Mighty Skill-Bridge の利用者問い合わせを、フォーム・暫定メール・課題管理表・GitHub Issues へ同じ基準で記録し、技術不具合、個人情報、請求、診断改善を取りこぼさない状態にする。

## 公式Docs確認

2026-06-16 のセッション開始時点で、以下の公式Docsを確認した。

- Firebase Hosting / Cloud Functions: https://firebase.google.com/docs/hosting / https://firebase.google.com/docs/functions
- Supabase getting started / RLS / migrations: https://supabase.com/docs/guides/getting-started / https://supabase.com/docs/guides/database/postgres/row-level-security / https://supabase.com/docs/guides/deployment/database-migrations
- Google Sheets batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions: https://docs.github.com/en/actions
- Slack Web API rate limits: https://docs.slack.dev/apis/web-api/rate-limits/
- Notion request limits: https://developers.notion.com/reference/request-limits

## 受付チャネル

| チャネル | 用途 | 正本 |
| --- | --- | --- |
| アプリ内フォーム | 通常問い合わせ、技術不具合、請求、個人情報、診断改善 | `support_requests` |
| 暫定メール | フォーム送信失敗時、添付が必要な場合、社内返信 | `k-umezawa@ml-mightylink.com` |
| 課題管理表 | 対応が必要な不具合・仕様変更・法務/請求確認 | `data/issues_tracker.tsv` |
| GitHub Issues | 開発対応・追跡が必要なもの | GitHub Issue + Project |
| Slack / Notion | 将来の通知・議事録・運用共有 | 月次/週次運用タスクで接続 |

将来的には会社管理の shared mailbox（例: `support@ml-mightylink.com`）へ移行する。現時点では会社提供 Google Workspace アカウントの `k-umezawa@ml-mightylink.com` を暫定窓口とする。

## 実装概要

### フロントエンド

`index.html` / `src/index.html` のフッター手前に問い合わせフォームを追加した。

- 種別: `general` / `technical` / `billing` / `privacy` / `feedback`
- 返信先メール: 必須、254文字上限
- 件名: 必須、3〜160文字
- 内容: 必須、10〜3000文字
- セッション識別子: 既存 feedback と同じ localStorage ランダムID

静的 GitHub Pages では `/api/support/request` が存在しないため送信失敗表示になる。Firebase/FastAPI 環境では API にPOSTされる。

### API

`src/app.py` に以下を追加した。

- `POST /api/support/request`
  - 公開送信用
  - expensive API レート制限対象
  - category / priority / email / subject / message length を検証
- `GET /api/support/summary`
  - Basic Auth必須
  - 総件数、status / priority / category 別件数、直近問い合わせの抜粋を返す

### データベース

`support_requests` テーブルを追加した。

- `category`: 問い合わせ分類
- `priority`: `normal` / `high` / `urgent`
- `contact_email`, `subject`, `message`
- `status`: `new` / `triaged` / `in_progress` / `escalated` / `closed`
- `source`, `page_url`, `session_id`, `metadata`, `created_at`, `updated_at`

追加ファイル:

- `db/migrations/postgres/20260616000001_support_requests.sql`
- `db/migrations/sqlite/20260616000001_support_requests.sql`
- `supabase/migrations/20260616000001_support_requests.sql`

Supabase側はRLSを有効化し、匿名REST公開ポリシーは作成しない。問い合わせ送信はFastAPI経由に限定する。

## SLA

| 優先度 | 条件 | 一次回答 | 対応方針 |
| --- | --- | --- | --- |
| P1 | サービス全体停止、認証全断、個人情報漏えい疑い、重大な課金事故 | 30分以内 | Incident Runbookへ接続し、CEO/開発担当へ即時共有 |
| P2 | AI診断不可、DB保存不可、技術不具合、個人情報/請求の確認 | 当日〜2時間以内 | `data/issues_tracker.tsv` と GitHub Issue に起票 |
| P3 | 通常問い合わせ、Sheets/Calendar同期遅延、軽微なUI不具合 | 1営業日以内 | 定例レビューまたは次回開発セッションで処理 |
| P4 | ドキュメント誤記、改善提案、診断品質コメント | 2〜5営業日以内 | QA表または月次品質レポートへ集約 |

## 運用手順

1. 管理者は毎営業日、Basic Auth付きで `GET /api/support/summary` を確認する。
2. `priority=urgent/high` または `category=technical/privacy/billing` は当日中に一次返信する。
3. 再現手順・仕様変更・法務確認・請求確認が必要なものは `data/issues_tracker.tsv` と GitHub Issues に起票する。
4. 顧客向け説明として再利用できる回答は `data/qa_tracker.tsv` に追加する。
5. 解決済みの問い合わせは `status=closed` へ更新する運用を、管理UIまたは運用スクリプト整備時に追加する。

## 確認コマンド

```powershell
python -m pytest tests/test_api.py tests/test_db_migration_management.py
python scripts/manage_db_migrations.py validate --engine sqlite
python scripts/manage_db_migrations.py validate --engine postgres
python scripts/manage_db_migrations.py validate --engine supabase
```

## プライバシーと注意点

- 問い合わせ本文に個人情報が入る可能性があるため、Sheets/Issue/Slack/Notionへ全文転載しない。
- `GET /api/support/summary` は管理者認証必須にし、本文は `message_excerpt` のみ返す。
- `support_requests` はSupabase RLS有効、anon REST公開なしで運用する。
- メール返信時は必要最小限の情報だけを引用し、添付ファイルや経歴書の再送を求める場合は保存期間と削除予定を明示する。
