# 勤務表自動解析・勤怠承認ワークフロー Runbook

- 対象WBS: T841
- 関連課題: R98
- 作成日: 2026-06-24
- レーン: Antigravity + Gemini / Codex / Claude Code
- 技術前提: フロントエンド `index.html`、バックエンド FastAPI on Firebase Functions、DB Supabase

## 結論

T841では、社内向け勤怠管理UIを、ジョブカン相当の簡易打刻保存、勤務表CSV解析、管理者承認ログへ接続した。社員名や社員番号そのもの、CSV原本、元ファイル名は保存せず、社内確認コードから作る匿名キーと集計メタデータだけを保存する。

## 保存する項目

| 項目 | 保存方法 |
| --- | --- |
| 社内確認コード | `ATTENDANCE_PSEUDONYM_SALT` とハッシュ化し `subject_pseudonym` のみ保存 |
| 打刻 | `clock_in` / `clock_out` / `break_start` / `break_end` と記録時刻 |
| 勤務表CSV | 原本は保存せず、ファイルdigest、拡張子、集計値だけ保存 |
| 集計値 | 実労働分、時間外労働分、休日出勤日数、深夜労働分、異常件数 |
| 承認 | `pending_approval` から `approved` / `rejected` へ更新し、管理者レビュー時刻を保存 |

## 保存しない項目

- 氏名、社員番号、メールアドレス、電話番号。
- CSV原本、PDF原本、元ファイル名。
- 勤怠データの生明細行。
- ジョブカンやGoogle Workspaceの認証情報、API key、token、secret。

## CSV形式

初期PoCではCSVまたはテキストCSVのみ対応する。PDFは原本保存やOCR誤読のリスクがあるため、T841では自動解析対象外とし、将来の外部OCR/Google Drive連携確認後に再判定する。

対応ヘッダ例:

```csv
date,work_hours,overtime_hours,midnight_hours,holiday_work,anomaly
2026-06-01,8.0,1.5,0,0,なし
2026-06-02,9.0,2.0,0.5,1,打刻漏れ
```

日本語ヘッダは `実労働時間`、`残業時間`、`深夜労働時間`、`休日出勤`、`打刻漏れ`、`異常` などを読み取る。

## API

### 打刻保存

`POST /api/attendance/punch`

```json
{
  "employee_identifier": "emp-2026-001",
  "event_type": "in",
  "consented": true,
  "source": "attendance_widget",
  "page_url": "/",
  "session_id": "browser-session-id"
}
```

### 勤務表CSV解析

`POST /api/attendance/timesheet/parse`

multipart form-data:

- `file`: CSVまたはテキストCSV
- `employee_identifier`
- `consented=true`
- `consent_version=MSB-ATTENDANCE-2026-06`
- `source`
- `page_url`
- `session_id`

成功時は `import_id`、`subject_pseudonym`、`approval_status=pending_approval`、集計値、privacy controlsを返す。

### 勤務表承認

`POST /api/attendance/timesheet/approve`

Basic Auth必須。

```json
{
  "import_id": 1,
  "decision": "approved"
}
```

### 管理者サマリー

`GET /api/attendance/summary`

Basic Auth必須。打刻件数、勤務表取込件数、承認状態別件数、承認済み平均、最近の取込だけを返す。

## Supabase適用

本番DBには `supabase/migrations/20260624000001_attendance_workflow.sql` を適用する。

- `public.attendance_punch_events` と `public.attendance_timesheet_imports` を作成する。
- RLSを有効化する。
- `anon` と `authenticated` の直接テーブル権限をrevokeする。
- 書き込み、解析、承認、summaryはFastAPI経由に限定する。

## 運用手順

1. 本番反映前に `ATTENDANCE_PSEUDONYM_SALT` を会社管理secretとして設定する。
2. 打刻/CSV解析前に同意チェックが必須であることを確認する。
3. 管理者承認はBasic Auth付きAPIで実施する。
4. Sheets、Issue、docs、NotebookLMへ個人別勤怠明細やCSV原本を転記しない。
5. ジョブカン本連携を行う場合は、T823/T836の会社アカウント移管とOAuth/管理者承認後に、secret非記録の接続Runbookを追加する。

## 検証

- `tests/test_api.py::test_attendance_punch_timesheet_parse_approval_and_summary`
- `python scripts/verify_public_demo.py --url https://mightylink-app.com/`

## 公式ドキュメント確認メモ

2026-06-24のセッションで、OpenAI Codex、Anthropic Claude Code、Google Gemini/Workspace、Firebase Hosting/Functions、Supabase RLS、GitHub Actions/Issues/Projects、Slack、Notion、Figma、Stripe、Discord、Firecrawl、お名前.com などの公式ドキュメントを確認した。T841には特に、Firebase FunctionsのAPI境界、Supabase RLS、Google Sheets batchUpdate、GitHub Projects、Claude Code/Codexの安全なセッション運用方針を反映した。
