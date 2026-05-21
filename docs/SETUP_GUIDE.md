# Mighty Skill-Bridge セットアップ・運用手順書

この手順書は、Mighty-Link AI Connect / Mighty Skill-Bridge のローカル実行、Google Workspace 連携、WBS 同期、共有作業を再現できるようにまとめたものです。

## 1. 現在の前提

- 実行アカウント: `k-umezawa@ml-mightylink.com`
- 共有先: `kobayashi-masami@ml-mightylink.com`
- Google Cloud プロジェクト: `mighty-link-ai-connect`
- 進捗管理スプレッドシート ID: `1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8`
- WBS カレンダー名: `Mighty Skill-Bridge 開発計画`
- ローカルサーバー: `http://localhost:8000`

詳細な移行作業ログは [GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md](GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md) を参照してください。
Gemini quota 制限中の Codex 継続運用は [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md) を参照してください。

## 2. フォルダ構成

```text
mighty-link-ai-connect/
├── src/
│   ├── app.py
│   └── index.html
├── scripts/
│   ├── sync_wbs_to_calendar.py
│   ├── sync_wbs_to_sheets.py
│   └── share_resources.py
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md
│   ├── CODEX_CONTINUATION_NOTES.md
│   ├── PROJECT_STRUCTURE.md
│   ├── WBS.md
│   ├── WBS_SYNC_GUIDE.md
│   ├── ANTIGRAVITY_GUIDE.md
│   ├── database.md
│   └── requirements.md
├── data/
│   └── WBS.tsv
├── exports/
│   └── mighty_development_plan.ics
├── credentials.json
├── client_secret.json
├── authorized_user.json
├── credentials.json.template
├── requirements.txt
├── README.md
└── .gitignore
```

認証ファイルはプロジェクトルート直下に置きます。`.gitignore` で Git 管理対象外にしているため、GitHub へアップロードしないでください。

## 3. 初回セットアップ

依存ライブラリをインストールします。

```powershell
pip install -r requirements.txt
```

Google Cloud Console 側では、以下の API と OAuth 設定が必要です。

- Google Sheets API
- Google Drive API
- Google Calendar API
- OAuth 2.0 デスクトップクライアント
- テストユーザー: `k-umezawa@ml-mightylink.com`

OAuth クライアント JSON は `client_secret.json` にリネームして、プロジェクトルートへ配置します。

## 4. 開発ツール切り替え方針

通常開発は Antigravity + Gemini で進めます。Antigravity 側で Gemini の baseline quota 制限に達した場合は、作業を止めずに VSCode + Codex へ切り替えて開発を継続します。

切り替え時の運用ルール:

- 実装、ドキュメント整備、ローカル検証、Git 操作は VSCode + Codex で継続する。
- Gemini API の quota を消費しないよう、必要に応じて `AI_FORCE_MOCK=1` で FastAPI を起動する。
- Google Workspace 連携は既存の `authorized_user.json` を使い、`k-umezawa@ml-mightylink.com` の OAuth 認証を継続利用する。
- quota 回復後に Gemini live 実行へ戻す場合は、`AI_FORCE_MOCK` を解除してサーバーを再起動する。

quota 制限時の詳細手順は [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md) を参照してください。

## 5. WBS を Google カレンダーへ同期

```powershell
python scripts/sync_wbs_to_calendar.py
```

初回実行時はブラウザが開きます。`k-umezawa@ml-mightylink.com` でログインし、カレンダー、スプレッドシート、Drive への権限を許可します。

成功すると次の状態になります。

- `Mighty Skill-Bridge 開発計画` カレンダーが作成または再利用されます。
- WBS 開発スケジュール全 6 件が同期されます。
- `exports/mighty_development_plan.ics` が生成されます。
- `authorized_user.json` がプロジェクトルートに保存され、次回以降は認証が自動化されます。

## 6. WBS を Google Sheets へ同期

既存の進捗管理スプレッドシートへ同期する場合:

```powershell
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
```

同期元データは [data/WBS.tsv](../data/WBS.tsv) です。

## 7. 小林社長へカレンダーと Sheets を共有

```powershell
python scripts/share_resources.py
```

このスクリプトは `authorized_user.json` の OAuth トークンを使い、以下を実行します。

- `Mighty Skill-Bridge 開発計画` カレンダーを `writer` 権限で共有
- 進捗管理スプレッドシートを `writer` 権限で共有

`File not found` が出る場合は、スプレッドシートのオーナー側から `k-umezawa@ml-mightylink.com` を編集者として共有してから再実行してください。

## 8. FastAPI サーバー起動

通常起動:

```powershell
python src/app.py
```

別ウィンドウを使わずバックグラウンド起動する場合:

```powershell
Start-Process -WindowStyle Hidden -FilePath python -ArgumentList "src/app.py" -WorkingDirectory .
```

ブラウザで `http://localhost:8000` を開き、画面の接続状態が `Live Connected` になることを確認します。

## 9. よくあるトラブル

### Gemini の quota 制限が出ている

Antigravity 側で Gemini の baseline quota 制限に達した場合は、VSCode + Codex で開発を継続します。Gemini API を消費しない `AI_FORCE_MOCK=1` で起動します。

```powershell
$env:AI_FORCE_MOCK = "1"
python src/app.py
```

この状態でも Sheets 連携と画面デモは継続できます。実装・検証作業は Codex 側で進めます。

### OAuth で「このアプリはブロックされています」と表示される

Google Cloud Console の対象プロジェクトで、OAuth 同意画面のテストユーザーに `k-umezawa@ml-mightylink.com` を追加します。

### スプレッドシート共有時に 404 File not found が出る

スプレッドシートのオーナー権限を持つアカウントから、`k-umezawa@ml-mightylink.com` を編集者として共有します。その後、`python scripts/share_resources.py` を再実行します。

### `Live Connected` にならない

`client_secret.json` と `authorized_user.json` がプロジェクトルート直下にあるか確認し、`python src/app.py` で起動し直します。
