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
│   ├── share_resources.py
│   └── verify_public_demo.py
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md
│   ├── CODEX_CONTINUATION_NOTES.md
│   ├── BACKEND_AI_PIPELINE.md
│   ├── CEO_PRESENTATION_PREP_2026-06-02.md
│   ├── PROJECT_STRUCTURE.md
│   ├── WBS.md
│   ├── WBS_SYNC_GUIDE.md
│   ├── ANTIGRAVITY_GUIDE.md
│   ├── database.md
│   └── requirements.md
├── data/
│   ├── WBS.tsv
│   └── audit/
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

現在の同期スクリプトは、参考ファイル `【次期CATS】WBS_分析計画工程(後半).xlsx` の構成を踏まえ、以下の 3 タブを自動生成します。

- `Mighty-Link WBS`: 階層WBS、フェーズ行、予定/進捗、アラート、固定ヘッダー、フィルタ付きの管理表
- `WBS Summary`: フェーズ別の総数、完了数、未着手数、完了率、期間の集計
- `WBS Timeline`: タスク別の開始日、終了日、予定工数、進捗率の横断確認表

## 7. 小林社長へカレンダーと Sheets を共有

```powershell
python scripts/share_resources.py
```

このスクリプトは `authorized_user.json` の OAuth トークンを使い、以下を実行します。

- `Mighty Skill-Bridge 開発計画` カレンダーを `writer` 権限で共有
- 進捗管理スプレッドシートを `writer` 権限で共有

`File not found` が出る場合は、スプレッドシートのオーナー側から `k-umezawa@ml-mightylink.com` を編集者として共有してから再実行してください。

## 8. 6/2 社長プレゼン準備

6/2 の社長打ち合わせまでは、実際の企画・サービス内容を決め打ちせず、判断材料・デモ・論点整理・決定後の反映準備を進めます。

準備ブリーフ:

- [CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md)

当日前後の必須確認:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

## 9. FastAPI サーバー起動

通常起動:

```powershell
python src/app.py
```

別ウィンドウを使わずバックグラウンド起動する場合:

```powershell
Start-Process -WindowStyle Hidden -FilePath python -ArgumentList "src/app.py" -WorkingDirectory .
```

ブラウザで `http://localhost:8000` を開き、画面の接続状態が `Live Connected` になることを確認します。

## 10. 公開デモURLのデグレ防止

社長共有済みの公開URL `https://kanta13jp1.github.io/mighty-link-ai-connect/` は GitHub Pages の本番デモ面として扱います。

重要ルール:

- ルート直下の `index.html` は削除・移動しない。
- FastAPI 用の `src/index.html` を変更する場合でも、公開URL用の `index.html` への影響を必ず確認する。
- push 前に `scripts/verify_public_demo.py` を実行し、README fallback や UI マーカー欠落がないことを確認する。
- `main` / `master` への push 時は GitHub Actions `Public Demo Guard` が root `index.html` を検証する。

ローカル検証:

```powershell
python scripts/verify_public_demo.py
```

公開URL反映後の検証:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

## 11. AI 監査ログの確認

`/api/parse` と `/api/match` の実行結果は、後から判定根拠を確認できるように `data/audit/ai_audit.jsonl` へ保存されます。ログ本体は `.gitignore` 対象で、Git には含めません。

直近ログを確認する場合:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/audit/recent?limit=10"
```

レスポンスには `audit_event_id`、AI mode、スコア、matched/missing skills、短い excerpt が含まれます。原文全文は保存しません。

## 12. よくあるトラブル

### Gemini の quota 制限が出ている

Antigravity 側で Gemini の baseline quota 制限に達した場合は、VSCode + Codex で開発を継続します。Gemini API を消費しない `AI_FORCE_MOCK=1` で起動します。

```powershell
$env:AI_FORCE_MOCK = "1"
python src/app.py
```

この状態でも Sheets 連携と画面デモは継続できます。実装・検証作業は Codex 側で進めます。
バックエンドの deterministic fallback と Gemini 復帰時の接続方針は [BACKEND_AI_PIPELINE.md](BACKEND_AI_PIPELINE.md) を参照してください。

### OAuth で「このアプリはブロックされています」と表示される

Google Cloud Console の対象プロジェクトで、OAuth 同意画面のテストユーザーに `k-umezawa@ml-mightylink.com` を追加します。

### スプレッドシート共有時に 404 File not found が出る

スプレッドシートのオーナー権限を持つアカウントから、`k-umezawa@ml-mightylink.com` を編集者として共有します。その後、`python scripts/share_resources.py` を再実行します。

### `Live Connected` にならない

`client_secret.json` と `authorized_user.json` がプロジェクトルート直下にあるか確認し、`python src/app.py` で起動し直します。
