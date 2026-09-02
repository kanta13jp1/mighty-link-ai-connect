# 営業メールAIマッチング hardening監査ログ (T817_7_1)

- レポートID: `SALES_EMAIL_HARDENING_T817_7_1`
- 実施日: 2026-07-08
- 判定: **attention** (9/10 仮説PASS)
- スコープ: PoCデータ/スキーマ/コード/証跡のオフラインhardening監査。バックアップはfull-DB pg_dumpが9テーブルを包含（恒久CI化はT870、暫定22テーブルローカルバックアップはT871確認済み）。実メール接続後の実運用確認（実データの最小化スポット確認・実流量調整・アカウント権限実査）はT836受領後のT817_7本体工程。

## 10仮説検証（hardening 6観点）

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | 営業メール9テーブル全てにRLSが有効化されている | PASS | RLS有効化 9/9 |
| H2 | 9テーブル全てでanon/authenticatedの権限が剥奪されている | PASS | REVOKE 9/9 |
| H3 | スキーマは生PII列を持たず、送信者/本文はhash+上限付きexcerptのみ保存する | PASS | 禁止列=なし hash列=True excerpt長CHECK=True |
| H4 | redact/excerptユーティリティがメール・電話・secret実値を除去し240字上限を守る | PASS | redact後PII残存なし=True excerpt長=240(<=240) |
| H5 | 取込は合成メールのPII実値を保存せず、sha256ハッシュとredacted excerptのみ残す | PASS | 生メール/電話の残存なし=True sender_hash/body_hash=sha256(64hex) |
| H6 | 抽出は要員を匿名化キーで扱い、evidenceに生連絡先を残さない | PASS | 生連絡先残存なし=True anonymized_talent_key=talent_318929b97f4d8873 |
| H7 | 営業メールAPI全3ルートがBasic認証necessary（verify_credentials）である | PASS | 認証必須 3/3 |
| H8 | 保持/削除runbookが9テーブル全ての保持期間と削除手順をカバーする | PASS | runbook記載 5/5グループ 保持期間記載=True |
| H9 | 負荷ガード: parse CLIは既定でバッチ上限を持ち、無制限のAPI呼び出しをしない | PASS | 既定cap=50(=50期待) --max-messages指定=10 |
| H10 | レビュー監査証跡(exports)が存在し、証跡ファイルに生メール/電話が含まれない | FAIL | 監査証跡欠落=なし 生PII検出=['exports/sales_email_extraction_review.md:m-takahashi@da-edu.com'] |

## 残作業（T817_7本体・T836実接続後）

- 実メールボックス接続後の実データPII最小化スポット確認と、実流量でのバッチ上限・クォータ調整。
- 実接続アカウントの権限実査（mailbox読み取り専用スコープ、service_role鍵の保管場所）。
- 本番Supabase上の9テーブルへのパイプライン経由書き込み検証（T845残工程と同一の運用者工程）。
