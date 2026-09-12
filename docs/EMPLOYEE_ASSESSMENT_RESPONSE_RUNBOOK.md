# 社内向け適性・状況アンケート回答保存 Runbook

- 対象WBS: T840
- 関連課題: R32, R36, R96, R98
- 作成日: 2026-06-24
- レーン: Antigravity + Gemini / Codex / Claude Code
- 技術前提: フロントエンド `index.html`、バックエンド FastAPI on Firebase Functions、DB Supabase

## 結論

T840では、社内向け適性・状況アンケートの初期UIを、同意付きの回答保存APIへ接続した。MightyLink本体は精神状態や健康状態をAI診断せず、本人が入力した社内確認コードを匿名キー化し、部署カテゴリ、モチベーション自己申告、カルチャーフィット自己申告、業務上の成長/支援メモだけを最小保存する。

## 保存する項目

| 項目 | 保存方法 |
| --- | --- |
| 社内確認コード | `EMPLOYEE_ASSESSMENT_PSEUDONYM_SALT` とハッシュ化し `subject_pseudonym` のみ保存 |
| 部署カテゴリ | 粗い `department_bucket` として保存 |
| モチベーション/カルチャー | 1から5の自己申告値として保存 |
| 自由記述 | メール、電話、secret-like値をredactし、最大1000文字の抜粋だけ保存 |
| 同意 | `consent_version`、`consented_at`、保存時刻、削除予定日を保存 |

## 保存しない項目

- 氏名、メールアドレス、電話番号、社員番号そのもの。
- 病歴、健康診断結果、精神疾患、治療方針などの健康・医療情報。
- 心理・健康系の生回答や外部サービスの個人別スコア。
- 採用、配属、評価、契約継続を自動決定するための判定結果。
- API key、password、token、secretなどの認証情報。

## API

### 回答保存

`POST /api/employee-assessment/responses`

```json
{
  "employee_identifier": "emp-2026-001",
  "department": "開発本部",
  "motivation_level": 4,
  "culture_level": 5,
  "growth_feedback": "FastAPI設計レビューの支援が必要です。",
  "consented": true,
  "consent_version": "MSB-EMP-ASSESS-2026-06",
  "source": "employee_assessment_form",
  "page_url": "/",
  "session_id": "browser-session-id"
}
```

成功時は `subject_pseudonym`、`response_id`、`deletion_due_at`、`privacy_controls` を返す。直接識別子は返さない。

### 管理者サマリー

`GET /api/employee-assessment/responses/summary`

Basic Auth必須。件数、平均値、部署カテゴリ別件数、redacted済み最近の回答だけを返す。

## Supabase適用

本番DBには `supabase/migrations/20260624000000_employee_assessment_responses.sql` を適用する。

- `public.employee_assessment_responses` を作成する。
- RLSを有効化する。
- `anon` と `authenticated` からの直接テーブル権限をrevokeする。
- 書き込みと管理者サマリーはFastAPI経由に限定する。

## 運用手順

1. 本番反映前に `EMPLOYEE_ASSESSMENT_PSEUDONYM_SALT` を会社管理secretとして設定する。
2. フォーム送信前に同意チェックが必須であることを確認する。
3. 管理者サマリーはBasic Auth経由で確認し、Sheets/Issue/docsへ個人別回答や生メモを転記しない。
4. 同意撤回、退職、PoC終了時は `subject_pseudonym` 単位で削除し、削除証跡だけを残す。
5. R36/T838/T839の法務・ベンダー確認が完了するまで、心理・健康スコア連携や自動評価用途へ拡張しない。

## 検証

- `tests/test_api.py::test_employee_assessment_response_submission_summary_and_redaction`
- `python scripts/verify_public_demo.py --url https://mightylink-app.com/`

## 公式ドキュメント確認メモ

2026-06-24のセッションで、OpenAI Codex、Anthropic Claude Code、Google Gemini/Workspace、Firebase、Supabase RLS、Microsoft Azure AI Foundry、GitHub Actions/Issues/Projects、Stripe、Slack、Notion、Figma、Unity、Apple HIG、AWS Bedrock、Meta Llama、xAI、Kimi、MiMo、DeepSeek、ByteDance Seedance、Obsidian、Canva、Reddit、InsForge、Firecrawl、Discord、お名前.com の公式ドキュメントを確認した。T840には特に、Supabase RLS、Firebase Hosting/Functions、Google Sheets batchUpdate、GitHub Issues/Projects、Claude Code memory/settings/security、Codex AGENTS.md/best practices/MCPの運用方針を反映した。
