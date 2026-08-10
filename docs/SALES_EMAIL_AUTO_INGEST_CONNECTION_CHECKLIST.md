# 営業メール自動取り込み 接続方式確認チェックリスト

- 作成日: 2026-06-20
- 関連WBS: T817, T817_7, T824, T922, T943
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

POP3しか使えない場合の最終候補。共有営業メールでは受信後のサーバー削除が営業機会の消失につながるため、本番自動取り込みでは使用しない。互換性確認で利用する場合も読み取り専用とし、削除命令を禁止する。

| 環境変数候補 | 内容 |
| :--- | :--- |
| `MAIL_CONNECTOR_TYPE` | `pop3` |
| `POP3_HOST` / `POP3_PORT` | POP3サーバーとポート |
| `POP3_USE_SSL` | `true` 推奨 |
| `POP3_USERNAME` / `POP3_PASSWORD` | 対象アカウント認証情報 |
| `POP3_LEAVE_ON_SERVER` | 必ず `true`。`false` は接続前にエラーとして拒否する |

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
6. 共有営業メールの本番同期はIMAPの `readonly=True` だけを使用し、既読化、移動、削除、`EXPUNGE` を行わない。
7. IMAP同期が0件または失敗でもPOP3へ自動フォールバックしない。
8. POP3コネクタは `DELE` を実装せず、`POP3_LEAVE_ON_SERVER=false` を接続前に拒否する。
9. IMAP接続・認証・folder選択に失敗した場合は0件成功へ変換せず、同期APIを500、定期ジョブを失敗として記録する。
10. 本番のIMAP認証情報はGitHub Actionsの専用secret `SALES_EMAIL_IMAP_ENV` から既存Functions環境へoverlayし、汎用の `FIREBASE_FUNCTIONS_DOTENV` と分離して更新する。

---

## 本番の自動同期

- 登録済みGitHub Actions workflow `uptime-monitor.yml`（Production Operations Monitor）の `sales-email-sync` jobが15分ごとに起動する。新規workflowがActions APIへ登録されなかったため、確実に稼働する既存workflowへ統合した。Firebase SchedulerはCI service accountのIAM policy更新権限が不足するため採用しない。
- 対象folderは `INBOX` のみ。1回あたり最新100通を読み取り、dedupe keyで登録済みメールを除外する。
- workflowのconcurrency groupで重複起動を抑制する。
- workflow内で一時SQLiteをmigrationし、読み取り専用IMAP取得と解析を行ってから、`SUPABASE_DB_URL` で本番PostgreSQLへ重複排除付き同期する。Functions内の一時SQLiteには依存しない。
- Functions deployでも汎用dotenv内の古い `SUPABASE_DB_URL` を除去し、GitHubの専用secretを引用符付きでoverlayする。公開analytics・matchesは本番PostgreSQLを正本とし、静的702通レポートへのフォールバックを正常状態とみなさない。
- 取得は `IMAP4_SSL`、port 993、`readonly=True` で行う。既読化、移動、削除、`EXPUNGE`、POP3フォールバックは行わない。
- 接続・解析・PostgreSQL同期のいずれかが失敗した場合はActions job失敗として記録する。IMAP失敗を `0件・success` として隠さない。
- 定期jobは `--require-messages` を指定し、読み取り専用INBOXが0通なら削除・保持インシデントとして失敗させる。手動APIの0件応答だけで正常判定しない。
- 緊急停止はGitHub Actionsで `Production Operations Monitor` をdisableする。この操作は同workflowの公開uptime監視も停止するため、停止理由を運用記録へ残す。

### 停止判定

1. GMO WebメールまたはThunderbirdで、`INBOX` の最新受信日時と件数を確認する。
2. 本番DB `sales_email_messages` の `max(received_at)` と件数を読み取り専用で確認する。
3. `/api/sales-email/analytics` の最新日付を確認する。
4. GMOに新着があり、本番DBが30分以上更新されない場合は停止として扱う。
5. `/api/sales-email/sync` が200かつ0件でも正常と決めつけない。T943以降はIMAP接続失敗なら500となるため、Functionsログで例外種別を確認する。

### 2026-08-10停止インシデント

- GMO `INBOX` は読み取り専用接続に成功し、2026-08-10受信の2通を確認した。
- 本番Supabaseは702通、`max(received_at)=2026-07-25` で停止していた。
- 公開analyticsも最新日付が2026-07-25で、本番同期APIはIMAP失敗を握り潰してHTTP 200・0件を返していた。
- 定期起動するschedulerが実装されていなかったため、自動取り込みは成立していなかった。
- T943でfail-closed化、15分GitHub Actions workflow、専用IMAP secret overlayを追加した。専用secretを追加する前に旧IMAPキーを除去し、dotenvの重複キーや `#` を含む未引用パスワードで古い・切り詰められた認証情報が採用されないようにした。Functions内の営業メール処理は一時SQLiteへ保存して本番Supabaseへ到達しないため、Actionsから一時SQLiteを経由してPostgreSQLへ同期する構成へ変更した。

---

## メール消失時の緊急対応

1. `/api/sales-email/sync` と自動同期ジョブを停止する。
2. Thunderbirdでフォルダーの最適化、修復、アカウント削除を行わず、プロファイルの `INBOX` と `INBOX.msf` を別フォルダーへコピーする。
3. 該当メールをMessage-IDで特定し、`.eml` として保全する。
4. 対象アカウントを設定した全端末・外部サービスを確認し、POP3受信を停止する。
5. メールパスワードを変更して不明なクライアントを切断し、認可したIMAPクライアントだけへ新しい認証情報を設定する。
6. GMOへ発生時刻、Message-ID、対象アドレスを伝え、POP3 `DELE` またはIMAP `EXPUNGE` の接続元調査を依頼する。
7. 削除経路が停止したことをテストメールで確認してから、保全した `.eml` をIMAP受信トレイへ復元する。

### Thunderbirdキャッシュからの本番DB復旧

サーバーから消失済みでも、最適化前のThunderbird `INBOX` mboxに本文が残っている場合は、必ずプロファイル外へコピーしてSHA-256一致を確認してから復旧する。元ファイルを直接処理しない。

```powershell
python scripts/recover_thunderbird_sales_emails.py `
  --mbox "C:\path\to\preserved\INBOX" `
  --since 2026-07-26
python scripts/parse_sales_emails.py --max-messages 0
python scripts/sync_sqlite_to_supabase.py
```

復旧ツールはmboxを読み取り専用で解析し、既存のdedupe key、本文redaction、ハッシュ保存を通して一時SQLiteへ登録する。Supabase同期後に件数、`max(received_at)`、案件・要員抽出数を読み取り専用で照合する。

---

## 公式ドキュメント確認

- Microsoft Graph messages: https://learn.microsoft.com/en-us/graph/api/user-list-messages
- Microsoft Graph delta query for messages: https://learn.microsoft.com/en-us/graph/delta-query-messages
- Microsoft Graph Outlook change notifications: https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview
- Gmail API guides: https://developers.google.com/workspace/gmail/api/guides
- Gmail API push notifications: https://developers.google.com/workspace/gmail/api/guides/push
- IMAP4rev2 RFC 9051: https://datatracker.ietf.org/doc/html/rfc9051
- Firebase scheduled functions: https://firebase.google.com/docs/functions/schedule-functions
- Amazon SES receiving email: https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html
