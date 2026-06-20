# Google Workspace OAuth 再認証 Runbook

作成日: 2026-06-21
対応 WBS: T825
対象: Sheets / Calendar / Drive / NotebookLM Docs 同期

## 目的

`authorized_user.json` の refresh token が失効または取り消された場合に、WBS、課題管理表、QA表、Calendar、NotebookLM向けDrive資料の同期を安全に復旧する。

Google公式OAuthドキュメントでは、refresh token はユーザーによる取り消し、長期間未使用、パスワード変更、token上限、管理者ポリシー、テスト公開状態の制限などで使えなくなる場合がある。同期スクリプトは `invalid_grant` / `expired or revoked` を検知したら、フォールバックで曖昧に進めず再認証を促す。

## 復旧手順

まず現在の認証状態を確認する。

```powershell
python scripts/verify_google_workspace_account.py
```

`Google Workspace OAuth token is expired or revoked` が表示された場合は、次を実行する。

```powershell
python scripts/verify_google_workspace_account.py --reauth
```

ブラウザでは会社提供の Google アカウント `k-umezawa@ml-mightylink.com` を選択し、Sheets / Drive / Calendar の権限を許可する。成功後、次の同期を再実行する。

```powershell
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/sync_docs_to_notebooklm.py --drive-only
```

## セキュリティルール

- `authorized_user.json`、`client_secret.json`、OAuth token、refresh token は GitHub、Sheets、Issue、NotebookLM、Slack、チャット本文へ記録しない。
- `authorized_user.json` はローカル端末専用の認証キャッシュとして扱う。
- 認証後は `python scripts/verify_google_workspace_account.py` を再実行し、実行主体が `k-umezawa@ml-mightylink.com` であることを確認する。
- NotebookLM CLI の `notebooklm login` は NotebookLM 操作用のブラウザ状態を保存する処理であり、Sheets / Calendar / Drive API の `authorized_user.json` 再認証とは別に扱う。

## Closeout 再開基準

次をすべて満たしたら、通常のセッション closeout を再開できる。

- `verify_google_workspace_account.py` が成功する。
- Sheets 同期が `Mighty-Link WBS`、`課題管理表`、`QA表` を更新する。
- Calendar 同期が完了済みWBSイベントを削除し、未完了イベントだけを残す。
- Drive / NotebookLM docs 同期が `exports/knowledge_flow/notebooklm_docs_manifest.json` を更新する。
