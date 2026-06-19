# 営業メールAIマッチング 人間レビュー・評価ログ Runbook

- 作成日: 2026-06-19
- 関連WBS: T817, T817_6
- 関連課題: R75, R82
- ステータス: T817_6 完了。採用/却下/補正/要確認のレビュー結果を、匿名候補者キーとredacted根拠だけでDB・JSON・Markdownへ保存できる。

---

## 目的

T817_5で生成した営業メールAIマッチング候補は、営業判断の補助であり、自動確定には使わない。T817_6では、人間が候補を確認し、`accepted`、`rejected`、`needs_review`、`corrected` のいずれかで評価ログを残す。

レビュー時もメール本文全文、個人メールアドレス、電話番号、token/API key風文字列は保存しない。候補者は `talent_<hash>` の匿名キーで扱い、公開資料・Sheets・NotebookLMへ個人連絡先を流さない。

## 正本ファイル

| 用途 | ファイル |
| --- | --- |
| レビュー補助モジュール | `src/sales_email_review.py` |
| CLI | `scripts/review_sales_email_match.py` |
| API | `POST /api/sales-email/reviews`, `GET /api/sales-email/reviews/summary` in `src/app.py` |
| DB保存先 | `project_requirements`, `talent_profiles_from_email`, `email_match_results`, `email_match_feedback` |
| レビュー成果物 | `exports/sales_email_review_log.json`, `exports/sales_email_review_log.md` |
| テスト | `tests/test_sales_email_review.py` |

## API

レビュー登録はBasic Auth必須。

```http
POST /api/sales-email/reviews
Authorization: Basic ...
Content-Type: application/json

{
  "match_key": "match_...",
  "feedback_status": "corrected",
  "corrected_score": 41,
  "corrected_notes": "SQL/Oracle不足。再確認が必要。",
  "corrected_fields": {"missing_skills": ["SQL", "Oracle"]},
  "next_action": "Oracle経験の証跡を確認する"
}
```

`feedback_status` は `accepted`、`rejected`、`needs_review`、`corrected` のみ許可する。`needs_review` は `email_match_results.review_status` では `pending` として保持し、`email_match_feedback.feedback_status` へ詳細を残す。

集計確認:

```http
GET /api/sales-email/reviews/summary?limit=20
Authorization: Basic ...
```

## CLI

ローカルでレビュー証跡を作る場合:

```powershell
python scripts/review_sales_email_match.py `
  --match-report exports\sales_email_match_review.json `
  --json-report exports\sales_email_review_log.json `
  --markdown-report exports\sales_email_review_log.md `
  --feedback-status needs_review `
  --notes "Java overlapはあるがSQL/Oracle不足のため営業連絡前に確認する" `
  --next-action "Oracle/SQL経験の証跡を確認する" `
  --replace
```

## DB保存方針

1. レビュー対象の `project_key` と `talent_key` から、安全な案件・匿名要員サマリをDBへ作成または再利用する。
2. `email_match_results.metadata.match_key` で候補ペアを識別し、重複レビュー時も同じmatch_resultへ紐づける。
3. `email_match_feedback` にレビュー履歴を追記し、補正スコア、補正メモ、次アクションを保存する。
4. API応答、DB metadata、JSON/Markdown成果物にはredacted済みレビューコメントだけを出力する。

## セキュリティ方針

- 公開RESTからの直接書き込みは使わず、FastAPIのBasic Auth付き管理API経由に限定する。
- Supabase側はT817_3のRLS/REVOKE方針を維持し、匿名RESTへ `email_match_feedback` を開放しない。
- レビューコメントのメールアドレス、電話番号、secret-like値は保存前に `<email:redacted>`、`<phone:redacted>`、`<secret:redacted>` へ置換する。
- `accepted` であっても、実メール接続後の保持/削除、監査、負荷、権限確認はT817_7で別途確認する。

## 検証

```powershell
python -m pytest tests/test_sales_email_review.py tests/test_sales_email_match.py -q
python -m pytest tests/test_sales_email_ingest.py tests/test_sales_email_extract.py tests/test_sales_email_match.py tests/test_sales_email_review.py tests/test_sales_email_schema_migrations.py tests/test_db_migration_management.py tests/test_rls_policies.py -q
```

検証観点:

- Basic Authなしでレビュー登録できない。
- 採用/却下/補正/要確認のレビューが保存できる。
- DBの `email_match_feedback` とJSON/Markdown成果物にレビュー履歴が残る。
- メールアドレス、電話番号、secret-like値がAPI応答・成果物へ混入しない。

## 次工程

- T817_7: 実メール接続後の保持/削除、監査ログ、負荷、バックアップ、アカウント権限、Go/No-Go再判定を行う。

## 公式ドキュメント確認メモ

- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase Python Client: https://supabase.com/docs/reference/python/introduction
- Supabase Production Checklist: https://supabase.com/docs/guides/deployment/going-into-prod
- Gmail API Guides: https://developers.google.com/workspace/gmail/api/guides
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions Docs: https://docs.github.com/actions
- OpenAI Codex Best Practices: https://developers.openai.com/codex/learn/best-practices
