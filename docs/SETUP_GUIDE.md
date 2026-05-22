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
│   ├── generate_knowledge_flow_demo.py
│   ├── share_resources.py
│   └── verify_public_demo.py
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md
│   ├── CODEX_CONTINUATION_NOTES.md
│   ├── BACKEND_AI_PIPELINE.md
│   ├── CEO_PRESENTATION_PREP_2026-06-02.md
│   ├── CEO_PRESENTATION_DECISION_PACK_2026-06-02.md
│   ├── DEVELOPMENT_KNOWLEDGE_FLOW.md
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
│   ├── mighty_development_plan.ics
│   └── knowledge_flow/
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
- WBS 開発スケジュールと 6/2 社長プレゼン準備イベントが同期されます。`data/WBS.tsv` で完了済みのWBSに紐づくイベントはGoogle Calendarから削除され、未完了・実行中・会議イベントだけが残ります。
- `exports/mighty_development_plan.ics` が生成されます。
- `authorized_user.json` がプロジェクトルートに保存され、次回以降は認証が自動化されます。
- `python scripts/verify_google_workspace_account.py` で、`authorized_user.json` が `k-umezawa@ml-mightylink.com` に紐づいていることを確認できます。
- Sheets / Calendar / FastAPI 同期は、実行前にDrive APIでアカウントを検証し、別アカウントの場合は停止します。

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
- [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md)
- [DEVELOPMENT_KNOWLEDGE_FLOW.md](DEVELOPMENT_KNOWLEDGE_FLOW.md)
- [INTEGRATION_DEMO_EVIDENCE_2026-06-02.md](INTEGRATION_DEMO_EVIDENCE_2026-06-02.md)

開発ナレッジ連携の位置づけ:

- NotebookLM: `docs/` とWBSを読み込み、社長説明前の要約・想定QA作成に使う候補。
- Slack: WBS同期、GitHub Actions、公開URL検証、レビュー依頼を短文で共有する候補。
- Notion: 6/2議事録、意思決定DB、バックログ、社長レビュー用ページの候補。
- Obsidian: ローカルの設計メモ、ADR、プロンプト改善案を蓄積する候補。

6/2 までは、これらを正式サービス機能として固定せず、導入優先順位と情報管理ルールを社長に確認する判断材料として扱います。秘密情報を含まない範囲では、Google Drive、Notion、GitHub Issues への実体連携証跡を残します。

実際に見せるための成果物生成:

```powershell
python scripts/generate_knowledge_flow_demo.py
```

生成される主なファイル:

- `exports/knowledge_flow/notebooklm_source_pack.md`
- `exports/knowledge_flow/notebooklm_source_pack.txt`
- `exports/knowledge_flow/notebooklm_presentation_brief.md`
- `exports/knowledge_flow/notebooklm_presentation_brief.txt`
- `exports/knowledge_flow/slack_ceo_update.md`
- `exports/knowledge_flow/notion_decision_log.csv`
- `exports/knowledge_flow/notion_backlog_import.csv`
- `exports/knowledge_flow/integration_evidence.md`
- `exports/knowledge_flow/obsidian_vault/`

CLI/MCPで実施した連携証跡:

- Google Docs化したNotebookLM source pack: `https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit`
- Google Docs化したNotebookLM presentation brief: `https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit`
- Google Docsは `python scripts/upload_notebooklm_docs_to_drive.py` で作成・更新し、`authorized_user.json` が `k-umezawa@ml-mightylink.com` に紐づくことを検証してからDrive APIへアップロードする。

docs配下をNotebookLM source候補として同期する場合:

```powershell
python scripts/sync_docs_to_notebooklm.py
```

NotebookLM CLIが認証切れの場合は、以下を実行してから再同期します。

```powershell
notebooklm login
python scripts/sync_docs_to_notebooklm.py
```

`notebooklm login` では `k-umezawa@ml-mightylink.com` を選択してください。同期状況は `exports/knowledge_flow/notebooklm_docs_manifest.json`、再認証手順は `exports/knowledge_flow/notebooklm_cli_next_steps.md` に保存されます。
- Notion証跡ページ: `https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951`
- GitHub Issues: `https://github.com/kanta13jp1/mighty-link-ai-connect/issues`
- GitHub Projectは `gh auth refresh -h github.com -s read:project -s project` 後に正式連携する。
- Slackは投稿先チャンネルと共有範囲を確認してから送信連携する。

FastAPI 起動中は、画面の「開発ナレッジ連携デモ」からも生成できます。

```text
POST /api/knowledge-flow/generate
GET  /api/knowledge-flow/status
```

当日前後の必須確認:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/verify_google_workspace_account.py
python scripts/generate_knowledge_flow_demo.py
gh issue list --state all --label ceo-demo
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

`sync_wbs_to_sheets.py` は `Mighty-Link WBS` / `WBS Summary` / `WBS Timeline` に加え、`data/issues_tracker.tsv` から `課題管理表`、`data/qa_tracker.tsv` から `QA表` も同時に更新します。課題やQAが発生した場合は、該当TSVを更新してから同じ同期コマンドを再実行してください。

三ツール開発体制では、各セッション開始時に [AGENTS.md](../AGENTS.md) / [CLAUDE.md](../CLAUDE.md) / [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) を確認し、Anthropic・OpenAI・Google・Microsoft・Meta・Amazon・Apple・Kimi/Moonshot・MiMo・DeepSeek・Grok/xAI・Seedance/ByteDance Seed・Obsidian・Unity公式Docsの最新版を確認してから作業します。各セッションの終了時は、WBSタスクを最低1件完了させ、Sheets/Calendar同期、commit、push、`main`/`master`反映まで行います。

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

### NotebookLM CLI のログインが途中で落ちる

`notebooklm login` がGoogle Accountsの画面遷移中断で失敗する場合は、Workspace専用の補助ログインを使います。

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py
python scripts/generate_ceo_presentation_deck.py
```

ブラウザでは `k-umezawa@ml-mightylink.com` を選択します。認証後、NotebookLMのホームが表示されたらターミナルでEnterを押すと、CLI用のstorage stateが保存されます。

NotebookLMで取得した社長向け草案をPowerPoint化する場合は、`scripts/generate_ceo_presentation_deck.py` を実行します。成果物は `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` に保存されます。

### スプレッドシート共有時に 404 File not found が出る

スプレッドシートのオーナー権限を持つアカウントから、`k-umezawa@ml-mightylink.com` を編集者として共有します。その後、`python scripts/share_resources.py` を再実行します。

### `Live Connected` にならない

`client_secret.json` と `authorized_user.json` がプロジェクトルート直下にあるか確認し、`python src/app.py` で起動し直します。

## 2026-05-22 追加: Seedance API 動画デモ

公開デモの第一画面は `exports/seedance_demo/mighty_skill_bridge_seedance_demo.mp4` を表示します。ローカル FastAPI 起動時は `/api/seedance/video-demo` から Seedance API へ接続できます。

```powershell
python scripts/generate_seedance_demo_video.py
$env:SEEDANCE_API_KEY = "<your seedance or modelark api key>"
$env:SEEDANCE_API_URL = "<seedance create task endpoint>"
$env:SEEDANCE_MODEL = "seedance-1-0-pro"
# タスク取得型APIの場合のみ:
$env:SEEDANCE_RESULT_API_URL_TEMPLATE = "<result endpoint with {task_id}>"
python src/app.py
```

APIキーやエンドポイントが未設定の場合、`/api/seedance/video-demo` は安全なローカル動画を返します。秘密情報は `client_secret.json` などと同じくGitへ含めません。

## 2026-05-22 Seedance API 400 debug note

For ModelArk Seedance 2.0, the local adapter now uses a content-task payload by default:

```powershell
$env:SEEDANCE_API_KEY = "<BytePlus ModelArk API key>"
$env:SEEDANCE_API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
$env:SEEDANCE_RESULT_API_URL_TEMPLATE = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}"
$env:SEEDANCE_MODEL = "dreamina-seedance-2-0-260128"
$env:SEEDANCE_API_ENABLED = "1"
```

`/api/seedance/video-demo` sends `content: [{type: "text", text: prompt}]`, `ratio`, and `duration`. If another BytePlus media endpoint requires the older `prompt` field, set this before starting FastAPI:

```powershell
$env:SEEDANCE_PAYLOAD_STYLE = "prompt_legacy"
```

After changing environment variables or pulling code, restart `python src/app.py`. A `fallback` response with `seedance_live: true` means credentials are loaded but BytePlus returned an API error; check `fallback_reason` for the provider response body.

## 2026-05-22 Seedance async result polling

ModelArk video generation is asynchronous. A successful create request can return a `task_id` before the generated video URL is ready. The local adapter now polls the result endpoint after task creation:

```powershell
$env:SEEDANCE_RESULT_API_URL_TEMPLATE = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}"
$env:SEEDANCE_POLL_TIMEOUT_SECONDS = "30"
$env:SEEDANCE_POLL_INTERVAL_SECONDS = "5"
python src/app.py
```

Check polling readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected fields:

```text
seedance_live: True
seedance_result_polling: True
seedance_poll_timeout_seconds: 30
```

If `fallback_reason` says the task was accepted but no URL was returned within the timeout, increase `SEEDANCE_POLL_TIMEOUT_SECONDS`, restart FastAPI, and retry.

The browser also continues polling after a `pending` response. It calls:

```text
/api/seedance/video-task/{task_id}
```

every 10 seconds for up to about 10 minutes, then replaces the preview video when a generated URL is returned. If DevTools still shows `task_status=running`, keep the page open or raise the polling window for longer generation jobs.

## 2026-05-22 Seedance cost guard and saved default video

Seedance API billing calls are disabled by default. Even if `SEEDANCE_API_KEY` is set, FastAPI returns the saved local video unless this flag is set before startup:

```powershell
$env:SEEDANCE_API_ENABLED = "1"
python src/app.py
```

For normal demos, leave `SEEDANCE_API_ENABLED` unset. The default video is:

```text
exports/seedance_demo/mighty_skill_bridge_seedance_demo.mp4
```

The generated Seedance result has been saved to that path, and the previous procedural fallback is kept at:

```text
exports/seedance_demo/mighty_skill_bridge_procedural_fallback.mp4
```

The UI exposes a `Download Video` button that downloads the currently displayed video. Token/resource usage should be checked from BytePlus Console:

```text
ModelArk > Usage
ModelArk > Model activation > Media > Dreamina-Seedance-2.0
```

The API response used by this demo does not currently expose token consumption, so the source of truth for spend is the BytePlus usage/resource-pack screens.
