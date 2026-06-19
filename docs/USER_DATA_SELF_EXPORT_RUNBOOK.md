# ユーザーデータセルフエクスポート Runbook

## 目的

T781では、サービス終了（EOL）、会社アカウント移行、個人情報の開示請求に備えて、利用者本人が自分のデータをJSONで取得できるPoCを追加した。管理者の手作業CSVに依存しすぎない状態を作り、将来の本番オンボーディング（T752）で所有者カラムを追加する前段の設計確認を兼ねる。

## API

| 項目 | 内容 |
| :--- | :--- |
| API | `GET /api/user-data/export` |
| 形式 | JSON attachment |
| 認証 | Firebase Auth bearer token 必須 |
| ローカル検証用 | `USER_DATA_EXPORT_ALLOW_MOCK=1` |
| 任意スコープ | `session_id=<browser session id>` |

例:

```powershell
$token = "<Firebase ID token>"
Invoke-WebRequest `
  -Uri "https://mightylink-app.com/api/user-data/export?session_id=<browser-session-id>" `
  -Headers @{ Authorization = "Bearer $token" } `
  -OutFile "mighty-link-user-data-export.json"
```

公開デモでは `MOCK_AUTH` を使うことがあるが、このエクスポートAPIは `USER_DATA_EXPORT_ALLOW_MOCK=1` を明示しない限りmock identityを使わない。個人データのエクスポートだけは、デモ利便性より本人確認を優先する。

## 画面

問い合わせ欄に「ユーザーデータ JSON」取得UIを追加した。Firebaseログイン実装後、ブラウザに保存されたID tokenを使って `GET /api/user-data/export` を呼び出し、JSONファイルをダウンロードする。

現在のPoCでは、次の保存キーを順に見る。

| Storage | Key |
| :--- | :--- |
| `localStorage` / `sessionStorage` | `mighty_firebase_id_token` |
| `localStorage` / `sessionStorage` | `firebase_id_token` |
| `localStorage` / `sessionStorage` | `idToken` |

トークンが無い場合、UIは「ログイン後に利用可」と表示してAPIを呼ばない。

## エクスポート対象

| Collection | スコープ |
| :--- | :--- |
| `support_requests` | Firebaseユーザーのメールアドレスと `contact_email` が一致する行 |
| `feedback_events` | 指定された `session_id` に一致する行 |
| `match_results` | エクスポート対象feedbackの `match_result_id` から参照できる行 |
| `engineers` | エクスポート対象matchの `engineer_id` から参照できる行 |
| `jobs` | エクスポート対象matchの `job_id` から参照できる行 |

各collectionは `USER_DATA_EXPORT_MAX_ROWS` 件を上限とする。

## 現在の制約

初期デモテーブルである `engineers`、`jobs`、`match_results` は、stable ownership columns導入前に作られている。そのためT781のPoCでは、指定 `session_id` のfeedbackから参照できる行だけをエクスポートする。

一般公開・有償ローンチ前には、T752で `owner_uid` / `tenant_id` を追加し、Firebase Authユーザーまたは会社テナント単位で確実にスコープできる状態にする。

## 検証

```powershell
pytest tests/test_user_data_export.py
```

期待結果:

- 既定ではFirebase本人確認なしのセルフエクスポートを拒否する。
- ローカルPoCモードでは、本人メール一致の問い合わせと指定sessionのfeedback-linked match dataだけを返す。
- `parsed_skills`、`interview_questions`、`metadata` などのJSON列は、文字列ではなく構造化JSONで返る。

## 運用手順

1. Firebase Authが有効で、利用者が有効なID tokenを取得できることを確認する。
2. 利用者本人に画面の「ユーザーデータ JSON」からダウンロードしてもらう。
3. 本人がログインできない場合は、[PERSONAL_INFO_DISCLOSURE_PROCEDURES.md](PERSONAL_INFO_DISCLOSURE_PROCEDURES.md) に従って管理者が監査付きで代理対応する。
4. 上限件数を超える場合は問い合わせとして受け付け、Supabaseから監査付きで個別エクスポートする。
5. エクスポートファイルはGitHub Issues、Google Sheets、NotebookLM、Slackへ添付しない。

