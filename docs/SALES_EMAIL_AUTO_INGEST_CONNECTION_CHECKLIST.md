# 営業メール自動取り込み 接続方式確認チェックリスト

- 作成日: 2026-06-20
- 関連WBS: T817, T817_7, T824
- 関連Issue: #115
- ステータス: 接続方式の決め打ち防止と、必要情報の確認項目を整理済み

---

## 目的

営業メールAIマッチングでは、手動コピペではなく受信メールを自動的にDBへ取り込む。ただし、受信環境を確認する前に Gmail、Microsoft 365、IMAP などの方式を推測で決めない。

本チェックリストは、実メール接続前に人間へ確認する項目と、方式別に必要な設定情報を整理する。メールアドレス、パスワード、OAuth secret、API key などの実値はこのリポジトリ、GitHub Issues、Google Sheets、NotebookLM、Slack、チャット本文へ記録しない。

---

## まず確認すること

| 確認項目 | 必要な回答 |
| :--- | :--- |
| 利用中のメールサービス | Microsoft 365 / Exchange、Google Workspace / Gmail、独自メールサーバー、レンタルサーバー、その他 |
| 対象メールアドレス | 共有営業アドレス、個人アドレス、メーリングリスト、転送専用アドレスのどれか |
| 管理者 | メール管理画面に入れる担当者、OAuthアプリ作成やIMAP許可を設定できる担当者 |
| 取り込み対象 | 全受信メール、特定フォルダ、特定ラベル、特定差出人、件名条件 |
| 取り込み頻度 | 5分ごとのポーリング、1時間ごと、Webhook/Push通知、手動実行 |
| 添付ファイル | 取り込む / 取り込まない / ファイル名だけ / PDFやExcelのみ |
| 既読・移動 | 取り込み後に既読化するか、専用フォルダへ移動するか、元メールを変更しないか |
| 保持期間 | メール本文、redacted本文、ハッシュ、抽出結果をそれぞれ何日保持するか |
| 監査要件 | 取得者、取得時刻、件数、失敗理由、削除履歴をどこまで残すか |
| 秘密情報の受け渡し | 1Password、Google Secret Manager、GitHub Secrets、環境変数など、チャット以外の安全な経路 |

---

## 方式別の必要情報

### Microsoft 365 / Exchange Online / Outlook

推奨は Microsoft Graph。差分同期は `messages/delta`、即時寄りの検知はchange notificationsを候補にする。

| 種別 | 設定項目 |
| :--- | :--- |
| テナント | Azure tenant ID、会社ドメイン、管理者連絡先 |
| アプリ | Azure App Registration の client ID、認証方式（client secret または証明書） |
| 権限 | `Mail.ReadBasic` / `Mail.Read` / application permission の要否、管理者同意の可否 |
| 対象メールボックス | user principal name、共有メールボックスアドレス、フォルダID |
| 同期方式 | `messages/delta` のdeltaLink保存、またはchange notificationsの通知URL |
| セキュリティ | client secret実値、証明書秘密鍵、refresh token はSecret管理へ保存 |

### Google Workspace / Gmail

Gmailは候補の一つであり、利用中メール環境がGoogle Workspaceだと確認できた場合だけ採用する。

| 種別 | 設定項目 |
| :--- | :--- |
| Workspace | ドメイン、対象メールアドレス、管理者連絡先 |
| OAuth | OAuth client ID/secret、利用スコープ、またはDomain-wide delegationの可否 |
| 対象 | ラベル、検索クエリ、対象フォルダ相当の条件 |
| 同期方式 | `users.messages.list` によるポーリング、またはGmail Push通知のPub/Sub topic |
| セキュリティ | OAuth secret、refresh token、Pub/Sub service account情報はSecret管理へ保存 |

### 汎用IMAP

Microsoft GraphやGmail APIが使えない場合の互換方式。IMAPは受信メール取得の標準方式だが、管理者がIMAPを許可しているか、MFA時にアプリパスワードが使えるかを事前確認する。

| 環境変数候補 | 内容 |
| :--- | :--- |
| `MAIL_CONNECTOR_TYPE` | `imap` |
| `IMAP_HOST` | IMAPサーバー名 |
| `IMAP_PORT` | 通常 `993`（SSL/TLS） |
| `IMAP_USE_SSL` | `true` 推奨 |
| `IMAP_USERNAME` | 対象メールボックスのログインユーザー名 |
| `IMAP_PASSWORD` | アプリパスワードまたは専用パスワード。通常ログインパスワードは避ける |
| `IMAP_FOLDER` | 例: `INBOX` |
| `IMAP_SEARCH_CRITERIA` | 例: `UNSEEN`、日付条件、件名条件 |
| `IMAP_IDLE_ENABLED` | IMAP IDLEによる待受可否 |
| `IMAP_POST_ACTION` | `none`、`mark_seen`、`move:<folder>` |

### POP3

POP3しか使えない場合の最終候補。既読や差分管理が弱いため、可能ならIMAP/API方式を優先する。

| 環境変数候補 | 内容 |
| :--- | :--- |
| `MAIL_CONNECTOR_TYPE` | `pop3` |
| `POP3_HOST` / `POP3_PORT` | POP3サーバーとポート |
| `POP3_USE_SSL` | `true` 推奨 |
| `POP3_USERNAME` / `POP3_PASSWORD` | 対象アカウント認証情報 |
| `POP3_LEAVE_ON_SERVER` | サーバー上にメールを残すか |

### Webhook / メール転送 / 受信サービス

メールサービスがWebhook、転送、SES inbound、SendGrid inbound parse等を使える場合の候補。受信時にHTTP POSTで取り込めるため、ポーリングが不要になる。

| 設定項目 | 内容 |
| :--- | :--- |
| 送信元 | 利用サービス名、転送元メールアドレス、受信ドメイン |
| 受信URL | Firebase Functions / Cloud Run / FastAPI のWebhook URL |
| 認証 | 署名検証secret、Basic Auth、mTLS、IP allowlist |
| Payload | MIME raw、JSON、添付ファイルの形式 |
| 再送 | retry回数、idempotency key、重複排除キー |

### ファイル監視

メールクライアントや管理画面から `.eml` / `.mbox` / CSV を定期エクスポートできる場合の暫定自動化。PoCや移行時に有効。

| 設定項目 | 内容 |
| :--- | :--- |
| 監視フォルダ | ローカル/共有フォルダ/Drive/OneDriveのパス |
| ファイル形式 | `.eml`、`.mbox`、`.txt`、CSV |
| 実行頻度 | タスクスケジューラ、cron、GitHub Actions不可の場合はローカル常駐 |
| 処理後 | `processed/` へ移動、ハッシュ記録、失敗ファイル隔離 |

---

## 実装で守るルール

1. 受信環境が確定するまで、Gmail API・Microsoft Graph・IMAPのどれかを前提にした実装を決めない。
2. すべての方式は `RawSalesEmail` へ変換してから `src/sales_email_ingest.py` へ渡す。
3. メール本文全文、パスワード、OAuth token、client secret、アプリパスワードはGitHub、Sheets、Issue、NotebookLM、Slackへ出さない。
4. DB保存はT817_3のRLS/REVOKE方針に従い、匿名REST直アクセスを開けない。
5. 抽出結果はT817_6の人間レビューを通すまで営業判断の確定情報にしない。

---

## 公式ドキュメント確認

- Microsoft Graph messages: https://learn.microsoft.com/en-us/graph/api/user-list-messages
- Microsoft Graph delta query for messages: https://learn.microsoft.com/en-us/graph/delta-query-messages
- Microsoft Graph Outlook change notifications: https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview
- Gmail API guides: https://developers.google.com/workspace/gmail/api/guides
- Gmail API push notifications: https://developers.google.com/workspace/gmail/api/guides/push
- IMAP4rev2 RFC 9051: https://datatracker.ietf.org/doc/html/rfc9051
- Amazon SES receiving email: https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html
