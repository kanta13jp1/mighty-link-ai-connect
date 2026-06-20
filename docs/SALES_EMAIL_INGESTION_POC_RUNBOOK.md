# 営業メール取り込みPoC Runbook

- 作成日: 2026-06-17
- 関連WBS: T817_2
- 関連Issue: #106
- 対象: 共有営業アドレスの実メール接続方式を確定する前に、`.eml`、`.txt`、CSVエクスポートで安全に取り込みと重複排除を検証するPoC

---

## 目的

2026-06-17の小林社長との打ち合わせで、営業全員が見られる共有営業アドレスに毎日約1,000通届く案件メール、要員提案メール、営業メールをAIマッチングの入力にする方針になった。

T817_2では、本番のメールサービス連携やSupabase保存に入る前に、ローカルのテストメールで次を確認する。実メール接続方式は、Microsoft 365 / Exchange Online、Google Workspace / Gmail、汎用IMAP、Webhook、ファイル監視などをヒアリングしてから決める。

- `.eml`、`.txt`、CSVの取り込みができる。
- 送信者、正規化件名、本文ハッシュで重複を判定できる。
- OAuthトークン、IMAP/POP3パスワード、アプリパスワード、API secret、メール本文全文、個人連絡先をGitHub、Sheets、Issue、NotebookLM、Slack、チャット本文へ出さない。
- T817_3で整備したSupabaseスキーマに渡せるメタ情報とハッシュを作れる。

---

## 実行方法

```powershell
python scripts/ingest_sales_emails.py `
  --input path\to\sales-mail-samples `
  --json-report exports\sales_email_ingest_review.json `
  --markdown-report exports\sales_email_ingest_review.md
```

`--input` は複数回指定できる。ディレクトリを指定した場合は、配下の `.eml`、`.txt`、`.csv` を再帰的に読み込む。

```powershell
python scripts/ingest_sales_emails.py --input sample1.eml --input sample2.csv
```

---

## 入力フォーマット

### `.eml`

標準的なメールエクスポートを読み込む。`From`、`Subject`、`Date`、`Message-ID`、`text/plain` 本文を優先して扱う。HTMLメールはタグ除去したテキストをフォールバックにする。

### `.txt`

先頭に次のヘッダがある場合はメタ情報として扱う。

```text
From: BP Sales <bp@example.com>
Subject: SQL Oracle project
Date: Wed, 17 Jun 2026 10:00:00 +0900

本文...
```

ヘッダがない場合は、ファイル名を件名候補として本文全体を読み込む。

### CSV

次の英語カラムを推奨する。

| column | 内容 |
| --- | --- |
| `sender` | 送信者 |
| `subject` | 件名 |
| `body` | 本文 |
| `received_at` | 受信日時 |
| `message_id` | Message-ID |

日本語の `差出人`、`件名`、`本文`、`受信日時`、`メッセージID` も読み取り対象にしている。

---

## 出力と個人情報保護

出力は `exports/sales_email_ingest_review.json` と `exports/sales_email_ingest_review.md`。

保存するもの:

- 入力件数、ユニーク件数、重複件数
- `dedupe_key`
- `sender_hash` と送信者ドメイン
- `message_id_hash`
- 正規化件名の短い表示
- 本文ハッシュ
- redaction済みの短い本文抜粋

保存しないもの:

- OAuthトークン
- API credentials / client secret
- IMAP/POP3パスワード、アプリパスワード
- メール本文全文
- 添付ファイル
- 送信者メールアドレス全文
- 電話番号、メールアドレス、secret-like文字列

---

## 重複判定

重複キーは次を連結してSHA-256化する。

1. 送信者メールアドレスまたは送信者文字列
2. `RE:` / `FW:` / `返信:` / `転送:` を除いた正規化件名
3. 引用行や署名以降を除いた本文のSHA-256

このため、同じBPから届いた同一案件の再送や返信付きメールを、T817_3で整備した `sales_email_messages` 保存前に検出できる。

---

## 実メール接続時の方針

T817_2のPoCはローカルファイルで検証し、実メール本文やOAuth状態はリポジトリへ保存しない。実メール接続方式は [SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md](SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md) の確認項目を埋めてから選定する。

Microsoft Graph、Gmail API、IMAP、POP3、Webhook、ファイル監視のどの方式でも、取得処理は `sales_email_ingest.py` に `RawSalesEmail` を渡すアダプタとして追加する。これにより、重複排除、redaction、レポート生成の挙動を接続方式に依存させない。

T817_4で `scripts/extract_sales_email_requirements.py` を追加したため、取り込み後は同じ `.eml`、`.txt`、CSV入力から案件要件、要員情報、スキルタグ、redacted根拠抜粋、信頼度を抽出できる。

---

## 接続方式を決める前に必要な情報

この情報は「項目名」だけを確認し、実値はチャットやIssueへ貼らない。

| 分類 | 必要情報 |
| --- | --- |
| 共通 | メールサービス名、対象メールアドレス、管理者、対象フォルダ/ラベル、取り込み頻度、添付ファイル方針、取り込み後の既読/移動方針 |
| Microsoft 365 / Exchange | tenant ID、app registration、client ID、権限、対象mailbox、folder ID、delta/webhook利用可否 |
| Google Workspace / Gmail | Workspaceドメイン、OAuth client、対象label/search query、Gmail Push通知利用可否 |
| IMAP | `IMAP_HOST`、`IMAP_PORT`、SSL/TLS、`IMAP_USERNAME`、アプリパスワード、対象folder、IDLE利用可否 |
| POP3 | POP3サーバー、SSL/TLS、ユーザー名、パスワード、サーバー上にメールを残すか |
| Webhook/転送 | Webhook URL、署名secret、payload形式、再送/idempotency方針 |

---

## 検証

```powershell
python -m pytest tests/test_sales_email_ingest.py -q
python scripts/ingest_sales_emails.py --input path\to\samples
```

検証時は、生成されたMarkdown/JSONにメール本文全文、OAuthトークン、電話番号、メールアドレスが含まれていないことを確認する。
