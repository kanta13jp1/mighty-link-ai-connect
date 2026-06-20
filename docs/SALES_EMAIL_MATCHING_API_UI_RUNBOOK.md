# 営業メールAIマッチング検索API/UI Runbook

- 作成日: 2026-06-19
- 関連WBS: T817, T817_5, T817_6
- 関連Issue: #110
- 関連課題: R75, R82, R83
- ステータス: T817_5 完了。T817_6で人間レビュー、評価ログ、`email_match_feedback` 保存も完了。本番hardeningはT817_7で実装する。

---

## 目的

T817_4で生成した安全な営業メール抽出レビューJSONを入力に、案件から候補人材、人材から候補案件を双方向にリストアップする。候補にはスコア、スキル一致、条件一致、根拠、不一致理由を付ける。

この段階では営業判断へ自動確定しない。すべての候補は `review_status=pending` とし、T817_6の `POST /api/sales-email/reviews` で人間レビューの採用、却下、要確認、補正を保存する。

## 正本ファイル

| 用途 | ファイル |
| --- | --- |
| マッチングサービス | `src/sales_email_match.py` |
| CLI | `scripts/build_sales_email_match_review.py` |
| API | `GET /api/sales-email/matches` in `src/app.py` |
| UI | `src/index.html`, `index.html` の案件候補比較ボード |
| テスト | `tests/test_sales_email_match.py`, `tests/test_sales_email_review.py` |
| 入力 | `exports/sales_email_extraction_review.json` |
| 出力 | `exports/sales_email_match_review.json`, `exports/sales_email_match_review.md` |
| 人間レビュー | `exports/sales_email_review_log.json`, `exports/sales_email_review_log.md` |

## API

```http
GET /api/sales-email/matches?direction=project_to_talent&skills=Java&min_score=1&limit=20
```

主なquery:

| query | 内容 |
| --- | --- |
| `direction` | `project_to_talent` または `talent_to_project` |
| `skills` | カンマ区切りのスキル条件 |
| `remote` | `remote`, `hybrid`, `onsite` など |
| `min_score` | 0〜100の最低スコア |
| `limit` | 最大100件 |
| `project_key` | 特定案件への絞り込み |
| `talent_key` | 特定匿名候補者への絞り込み |

返却内容:

- `projects`: 案件要件の安全な要約
- `talents`: 匿名化済み候補者の安全な要約
- `matches`: 候補ペア、score、score_breakdown、matched_skills、missing_skills、matched_conditions、mismatch_reasons、match_reason

## UI

案件候補比較ボードは、`/api/sales-email/matches` が成功した場合に営業メール由来の案件と匿名候補者を優先表示する。APIが使えない場合は既存のデモ候補にfallbackする。

テーブルには以下を表示する:

- 候補者
- 総合マッチ度
- スキル適合
- 条件適合
- 根拠信頼度
- 尚可スキル適合
- 一致根拠
- 確認/不足

CSVエクスポートにも根拠と確認ポイントを含める。

## セキュリティ方針

1. 入力JSONに `raw_email_body_not_written`, `email_phone_secret_patterns_redacted_from_evidence`, `talent_identity_anonymized` がない場合はAPI/CLIで拒否する。
2. マッチング処理ではメール本文全文を読まない。T817_4のredacted evidenceと構造化項目だけを使う。
3. UI表示は匿名候補者キーを使い、氏名や連絡先は表示しない。
4. `review_status=pending` を維持し、人間レビュー前に営業利用の確定判断へ使わない。レビュー後も実メール接続後の運用hardeningが終わるまでは公開・有償利用へ使わない。
5. 実メール接続後もNotebookLM、GitHub、Sheetsへ本文全文や個人連絡先を同期しない。

## 実行方法

```powershell
python scripts/build_sales_email_match_review.py `
  --input-report exports\sales_email_extraction_review.json `
  --json-report exports\sales_email_match_review.json `
  --markdown-report exports\sales_email_match_review.md `
  --direction project_to_talent `
  --skills Java `
  --limit 20
```

## 検証

```powershell
python -m pytest tests/test_sales_email_match.py -q
python -m pytest tests/test_sales_email_ingest.py tests/test_sales_email_extract.py tests/test_sales_email_match.py tests/test_sales_email_schema_migrations.py tests/test_db_migration_management.py tests/test_rls_policies.py -q
```

検証観点:

- 案件と匿名候補者の候補ペアを生成できる。
- スキルフィルタと最低スコアで絞り込める。
- API応答とCLI出力に個人メール、電話番号、secret-like値が出ない。
- UIが営業メール候補を優先し、APIが使えない場合は既存デモへfallbackする。

## 次工程

- T817_6: 完了。人間レビューで採用/却下/要確認/補正を保存し、`email_match_feedback` とredacted評価ログへ接続済み。
- T817_7: 実メール接続後の保持/削除、監査ログ、負荷、アカウント権限、Go/No-Goを確認する。

## 公式ドキュメント確認メモ

- OpenAI Codex Best Practices: https://developers.openai.com/codex/learn/best-practices
- Gemini API Models: https://ai.google.dev/gemini-api/docs/models
- 営業メール自動取り込み 接続方式確認チェックリスト: [SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md](SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md)
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
