# 営業メールAI抽出パイプライン Runbook

- 作成日: 2026-06-19
- 関連WBS: T817, T817_4
- 関連Issue: #109
- 関連課題: R75, R81
- ステータス: T817_4 完了。T817_5のAPI/UI、T817_6の人間レビュー保存も完了。本番hardeningはT817_7で実装する。

---

## 目的

T817_2で安全に取り込んだ営業メールを、T817_3で整備したSupabaseスキーマへ渡せる構造化レコードに変換する。対象は案件要件、要員情報、スキルタグ、根拠抜粋、信頼度、fallback利用有無である。

今回のT817_4では、外部AI APIキーがなくても動く `deterministic-sales-email-extractor-v1` を実装した。Gemini APIなどのモデル接続は後続で差し替え可能だが、モデル障害時も同じ出力形を維持する。

## 正本ファイル

| 用途 | ファイル |
| --- | --- |
| 抽出ロジック | `src/sales_email_extract.py` |
| CLI | `scripts/extract_sales_email_requirements.py` |
| テスト | `tests/test_sales_email_extract.py` |
| 入力PoC | `src/sales_email_ingest.py` |
| DBスキーマ | `docs/SALES_EMAIL_DATABASE_SCHEMA_RUNBOOK.md` |

## 抽出項目

| 種別 | 項目 |
| --- | --- |
| 共通 | `dedupe_key`, `sender_domain`, `normalized_subject`, `email_kind`, `model_name`, `fallback_used` |
| 案件要件 | title, summary, required_skills, nice_to_have_skills, skill_categories, rate_min/max, location, remote_type, start_date_text, duration_text, commercial_flow, restrictions, evidence_excerpt, confidence |
| 要員情報 | anonymized_talent_key, summary, skills, skill_categories, experience_years, desired_rate_min/max, desired_location, remote_preference, availability_text, evidence_excerpt, confidence |
| スキルタグ | skill_name, skill_category, importance, confidence, evidence_excerpt |

## セキュリティ方針

1. 出力JSON/Markdownへメール本文全文を保存しない。
2. メールアドレス、電話番号、`token=` や `Bearer` などのsecret-like値は根拠抜粋でredactする。
3. 要員情報は `talent_<hash>` の匿名キーで扱い、個人名や本人連絡先を正本化しない。
4. 抽出結果の `review_status` は `pending` とし、人間レビューなしに `confirmed` へしない。
5. Gemini APIなど外部モデルを接続する場合も、promptやログへ実メール全文を残さない。必要最小限のredacted text、ハッシュ、構造化項目だけを送る。

## 実行方法

```powershell
python scripts/extract_sales_email_requirements.py `
  --input path\to\sales-mail-samples `
  --json-report exports\sales_email_extraction_review.json `
  --markdown-report exports\sales_email_extraction_review.md
```

`--input` はT817_2と同じく `.eml`、`.txt`、CSV、またはディレクトリを受け付ける。

## 検証

```powershell
python -m pytest tests/test_sales_email_extract.py -q
python -m pytest tests/test_sales_email_ingest.py tests/test_sales_email_extract.py tests/test_sales_email_schema_migrations.py tests/test_db_migration_management.py tests/test_rls_policies.py -q
```

検証観点:

- 案件メールから必須/尚可スキル、単価、勤務地、リモート条件、稼働時期、商流、制限を抽出できる。
- 要員提案メールから匿名要員キー、経験年数、希望単価、スキル、稼働可能時期を抽出できる。
- Markdown/JSONにメール本文全文、個人メールアドレス、電話番号、secret-like値が出ない。
- fallback利用時もDB投入しやすい構造を保つ。

## 次工程

- T817_5: 完了。`sales_email_extraction_review.json` 相当の構造をAPI/UIで検索し、案件→人材、人材→案件の双方向候補リストを表示する。
- T817_6: 完了。人間レビューで抽出結果を採用/却下/要確認/補正し、`email_match_feedback` とredacted評価ログへ接続済み。
- T817_7: 実メール接続、保持/削除、監査ログ、負荷、アカウント権限、Go/No-Goを確認する。

## 公式ドキュメント確認メモ

- Gemini API Models: https://ai.google.dev/gemini-api/docs/models
- Gemini API Context Caching: https://ai.google.dev/gemini-api/docs/caching
- Gmail API Guides: https://developers.google.com/workspace/gmail/api/guides
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- OpenAI Codex Best Practices: https://developers.openai.com/codex/learn/best-practices
