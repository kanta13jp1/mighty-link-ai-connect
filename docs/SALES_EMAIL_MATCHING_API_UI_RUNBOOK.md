# 営業メールAIマッチング検索API/UI Runbook

- 作成日: 2026-06-19
- 関連WBS: T817, T817_5, T817_6, T920, T923, T1006
- 関連Issue: #110, #331
- 関連課題: R75, R82, R83, R152
- ステータス: T817_5 完了。T817_6で人間レビュー、評価ログ、`email_match_feedback` 保存も完了。T920で必須スキル、単価範囲、フリーワード、適合度、T923で案件メール受信日の期間絞り込みを追加。T1006で`limit`適用後の候補に関係する案件・人材要約だけを返すよう応答サイズを縮小。本番hardeningはT817_7で実装する。

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
GET /api/sales-email/matches?direction=project_to_talent&skills=Java&min_rate=60&max_rate=90&search_query=AWS&received_from=2026-07-01&received_to=2026-07-31&min_score=80&limit=20
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
| `min_rate` | 案件単価レンジの下限条件（万円/月）。案件上限がこの値未満の場合は除外 |
| `max_rate` | 案件単価レンジの上限条件（万円/月）。案件下限がこの値を超える場合は除外 |
| `search_query` | 案件名、匿名要員ラベル、構造化スキル、送信元ドメイン、redacted evidence の部分一致 |
| `received_from` | 案件メール受信日の開始日。JST基準の `YYYY-MM-DD` |
| `received_to` | 案件メール受信日の終了日。JST基準の `YYYY-MM-DD` |

`min_rate` / `max_rate` は案件単価レンジとの重なりで判定する。単価条件を指定した場合、単価が未抽出の案件は誤認防止のため除外する。下限が上限を超える場合や負数は `400` で拒否する。

`received_from` / `received_to` は案件メールの受信日を両端含みで判定する。元日時がRFC 2822またはISO形式でもJSTへ正規化し、期間指定時の日付不明案件は除外する。開始日が終了日を超える場合や実在しない日付は `400` で拒否する。期間判定は `limit` 適用前に行う。

返却内容:

- `project_count` / `talent_count`: フィルター適用後、`limit`適用前の取得元カタログ総数
- `projects`: 返却する`matches`から参照される案件要件だけを含む安全な要約
- `talents`: 返却する`matches`から参照される匿名候補者だけを含む安全な要約
- `matches`: 候補ペア、score、score_breakdown、matched_skills、missing_skills、matched_conditions、mismatch_reasons、match_reason

`limit`は`matches`だけでなく、応答へ同梱する`projects` / `talents`の参照範囲にも連動する。総数表示の互換性は`project_count` / `talent_count`で維持し、返却候補と無関係なカタログ全量は送信しない。T1006の本番相当データによるローカル計測では、`limit=1`のJSON応答を1,362,338 bytes相当から5,373 bytesへ縮小した。

## UI

案件候補比較ボードは、`/api/sales-email/matches` が成功した場合に営業メール由来の案件と匿名候補者を優先表示する。APIが使えない場合は既存のデモ候補にfallbackする。

公開マッチング進捗テーブルの上部では、フリーワード、案件の必須スキル、単価下限/上限、適合度、案件メール受信日の開始日/終了日で絞り込む。受信日を変更した場合はAPIで期間を先に適用し、それ以外の条件は取得済み候補へリアルタイムに適用する。件数表示は「表示中 / 取得済み全件」を示す。条件に一致しない場合は0件表示を維持し、デモ候補へ戻さない。リセットボタンで全条件を解除してAPIを再取得する。

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
python -m pytest tests/test_sales_email_match.py tests/test_public_matching_filters.py -q
python -m pytest tests/test_sales_email_ingest.py tests/test_sales_email_extract.py tests/test_sales_email_match.py tests/test_sales_email_schema_migrations.py tests/test_db_migration_management.py tests/test_rls_policies.py -q
```

検証観点:

- 案件と匿名候補者の候補ペアを生成できる。
- スキルフィルタと最低スコアで絞り込める。
- 単価レンジ、送信元ドメインを含むフリーワード、必須スキルで絞り込める。
- 案件メール受信日の開始日/終了日で絞り込め、一覧の受信日列と一致する。
- JSTへの日付正規化、期間端の包含、不正期間の400拒否が正しい。
- 単価不明案件は単価指定時に除外され、0件の結果がデモ行へ戻らない。
- API応答とCLI出力に個人メール、電話番号、secret-like値が出ない。
- `limit=1`で`matches`が最大1件となり、`projects` / `talents`がその候補から参照されるレコードだけを含み、JSON応答が100KB未満になる。
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
