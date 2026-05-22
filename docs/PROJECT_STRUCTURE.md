# プロジェクト構成方針

Mighty-Link AI Connect は、ローカル Web アプリ、Google API 連携スクリプト、設計ドキュメント、同期データが同居するプロジェクトです。ファイル数が増えてきたため、以下の責務で整理します。

## 現在の構成

```text
mighty-link-ai-connect/
├── src/          # FastAPI とフロントエンド
├── scripts/      # Google API 同期・共有・公開デモ検証などの運用スクリプト
├── .github/      # GitHub Actions による公開デモ保護
├── docs/         # 要件、設計、手順、作業ログ
├── data/         # 同期元データ、ローカル監査ログ
├── exports/      # 生成ファイル、外部取り込み用ファイル、検証スクリーンショット
├── AGENTS.md     # Codex / multi-agent 共通のプロジェクト指示
├── CLAUDE.md     # Claude Code 用 project memory entrypoint
├── requirements.txt
├── credentials.json.template
└── README.md
```

## 配置ルール

| 種別 | 配置先 | 例 |
| --- | --- | --- |
| アプリ本体 | `src/` | `app.py`, `index.html` |
| 運用スクリプト | `scripts/` | `sync_wbs_to_calendar.py`, `generate_knowledge_flow_demo.py`, `generate_ceo_presentation_deck.py`, `upload_notebooklm_docs_to_drive.py`, `sync_docs_to_notebooklm.py`, `notebooklm_login_workspace.py`, `generate_seedance_demo_video.py`, `render_seedance_video_demo_ui.py`, `share_resources.py`, `verify_public_demo.py` |
| CI ガード | `.github/workflows/` | `public-demo-guard.yml` |
| 仕様・手順 | `docs/` | `SETUP_GUIDE.md`, `BACKEND_AI_PIPELINE.md`, `CEO_PRESENTATION_PREP_2026-06-02.md`, `CEO_PRESENTATION_DECISION_PACK_2026-06-02.md`, `DEVELOPMENT_KNOWLEDGE_FLOW.md`, `INTEGRATION_DEMO_EVIDENCE_2026-06-02.md`, `requirements.md`, `database.md` |
| 同期元データ | `data/` | `WBS.tsv`, `issues_tracker.tsv`, `qa_tracker.tsv` |
| 実行時監査ログ | `data/audit/` | `.gitkeep`, `ai_audit.jsonl` (Git 管理対象外) |
| 生成物 | `exports/` | `mighty_development_plan.ics`, `knowledge_flow/`, `seedance_demo/` |
| 検証証跡 | `exports/verification/` | `seedance_video_desktop.png`, `seedance_video_mobile.png`, `seedance_refresh_desktop.png`, `seedance_refresh_mobile.png` |
| AIエージェント指示 | ルート直下 | `AGENTS.md`, `CLAUDE.md` |
| 認証情報 | ルート直下 | `client_secret.json`, `authorized_user.json` |

## 認証ファイルの扱い

以下はプロジェクトルート直下に置きます。スクリプトと FastAPI サーバーはこの前提で参照します。

- `client_secret.json`
- `credentials.json`
- `authorized_user.json`

これらは `.gitignore` の対象です。テンプレートとして共有する場合は `credentials.json.template` のようなダミー値のファイルだけを使います。

## 今後の拡張候補

- `tests/`: API と同期スクリプトの自動テストを追加する場合。
- `assets/`: 画像、ロゴ、サンプル PDF などを追加する場合。
- `config/`: 共有先メール、スプレッドシート ID、カレンダー名を外部設定化する場合。
- `logs/`: 手動実行ログを保存したい場合。ただし Git 管理対象にはしない。
- `data/audit/`: API 判定ログの置き場。`.jsonl` は Git 管理せず、`.gitkeep` だけでディレクトリを維持する。
- Obsidian vault を置く場合は、原則として本リポジトリ外に配置する。リポジトリ内へ置く場合は `docs/` に昇格した公式メモだけを Git 管理し、未整理メモや秘密情報は含めない。
- Notion / Slack / NotebookLM 連携は、6/2 の社長判断後に `config/` または環境変数で外部設定化する。
- `exports/knowledge_flow/` は社長説明用の安全なデモ成果物として Git 管理する。認証情報や個人情報は含めない。
- `exports/seedance_demo/` は公開URLでも表示できるプロジェクト生成動画を管理する。Seedance APIキーや外部レスポンスは含めない。
- `favicon.ico` はGitHub PagesとFastAPIローカル画面で共通利用するブランドアイコンとしてルートに置く。
- Chrome DevTools の `/.well-known/appspecific/com.chrome.devtools.json` はFastAPIが動的に返す。ローカル開発専用で、GitHub Pages用の静的ファイルとしては置かない。
- `data/external_api_usage.jsonl` はローカルの外部API利用台帳で、Git管理対象外。`/admin` と `/api/admin/usage` から確認する。
- `exports/verification/` は公開デモやローカルUIの視覚確認スクリーンショットを保存する。社長説明に使えるものだけをGit管理し、個人情報や認証画面は含めない。
- `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` はNotebookLM CLIの草案を社長説明用PPTXにした成果物として管理する。再生成は `scripts/generate_ceo_presentation_deck.py` で行う。
- GitHub Issues は実装タスクの粒度、WBS は日程・報告粒度として使い分ける。GitHub Project は `read:project` スコープ復旧後にIssue配置を行う。
- `AGENTS.md` はAntigravity + Gemini / VSCode + Codex / VSCode + Claude Codeの共通セッションゲートを定義する。`CLAUDE.md` はAnthropic公式推奨に従い `@AGENTS.md` を import する。
- 毎セッションの公式Docs確認は、Anthropic、OpenAI、Google、Microsoft、Meta、Amazon、Apple、Kimi/Moonshot、MiMo、DeepSeek、Grok/xAI、Seedance/ByteDance Seed、Obsidian、Unity を対象にする。URL正本は `AGENTS.md` に集約し、未確認の未来モデル名や古いベストプラクティスはdocsへ残さない。
- `.claude/settings.local.json` と `CLAUDE.local.md` はローカル専用設定として `.gitignore` 対象にし、共有すべき指示は `AGENTS.md` / `CLAUDE.md` / `docs/` へ昇格する。
- Google Sheets同期は `sync_wbs_to_sheets.py` 1本で `Mighty-Link WBS` / `WBS Summary` / `WBS Timeline` / `課題管理表` / `QA表` を更新する。
- Google Calendar同期は `sync_wbs_to_calendar.py` 1本で `data/WBS.tsv` の完了状態を読み、完了済みWBSに紐づくイベントをCalendarから削除し、未完了・実行中・会議イベントだけを残す。完了履歴はSheets/Docs/Git履歴で追跡する。
- 内容が古くなったdocsは、追記で温存せず削除または現在形へ置換する。削除判断は「公式Docsで裏取りできない未来モデル名」「現状と違う同期件数」「解決済みブロッカーを現行リスクとして扱う記述」「CEOに見せる導線を誤らせる古いIssue番号」を優先する。

## 実行コマンド

```powershell
python src/app.py
python scripts/verify_public_demo.py
python scripts/sync_wbs_to_calendar.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/generate_knowledge_flow_demo.py
python scripts/generate_ceo_presentation_deck.py
python scripts/notebooklm_login_workspace.py
python scripts/upload_notebooklm_docs_to_drive.py
python scripts/sync_docs_to_notebooklm.py
python scripts/share_resources.py
```
