# Mighty-Link AI Connect

Mighty Skill-Bridge は、エンジニア経歴書と案件情報の AI フィット診断、WBS 管理、Google Workspace 連携を行うローカルプロトタイプです。

## Quick Start

```powershell
pip install -r requirements.txt
python src/app.py
```

ブラウザで `http://localhost:8000` を開きます。

公開デモURLを変更前後に確認する場合:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

NotebookLM / Slack / Notion / Obsidian の社長説明用デモ成果物を生成する場合:

```powershell
python scripts/generate_knowledge_flow_demo.py
python scripts/generate_ceo_presentation_deck.py
```

CLI/MCPで実施した連携証跡は `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md` にまとめています。
NotebookLMでプレゼン資料のたたき台を作るための入力資料は `exports/knowledge_flow/notebooklm_presentation_brief.md` に生成されます。
NotebookLM CLIのCEO Slide OutlineをPowerPoint化した成果物は `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` です。

Google Workspace 連携アカウントを確認する場合:

```powershell
python scripts/verify_google_workspace_account.py
```

## Documents

- [セットアップ・運用手順書](docs/SETUP_GUIDE.md)
- [Antigravity 2.0 開発ガイド](docs/ANTIGRAVITY_GUIDE.md)
- [Multi-AI 開発ワークフロー (3-tool 体制)](docs/MULTI_AI_WORKFLOW.md) - Antigravity+Gemini / VSCode+Codex / VSCode+Claude Code の役割分担と handoff 規約
- [Google Workspace 移行・共有作業手順書](docs/GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md)
- [Codex 継続作業メモ](docs/CODEX_CONTINUATION_NOTES.md)
- [Backend AI Pipeline 設計メモ](docs/BACKEND_AI_PIPELINE.md) - deterministic fallback と AI 監査ログ
- [6/2 社長打ち合わせ プレゼン準備ブリーフ](docs/CEO_PRESENTATION_PREP_2026-06-02.md)
- [6/2 社長打ち合わせ 判断材料パック](docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md)
- [6/2 社長打ち合わせ 論点・選択肢・確認質問リスト](docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) - T605 deliverable
- [6/2 社長打ち合わせ 想定 QA パック](docs/CEO_PRESENTATION_QA_PACK_2026-06-02.md) - T607 deliverable
- [6/2 社長打ち合わせ 運用・体制・リスク・費用感 論点](docs/CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) - T606 deliverable
- [6/2 決定後ロードマップ枠](docs/CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) - T615 deliverable
- [6/2 社長 事前共有メモ + 当日アジェンダ短文](docs/CEO_PRESENTATION_PRESHARE_MEMO_2026-06-02.md) - T614 deliverable
- [6/2 社長プレゼン Canva / Figma リデザイン手順 + 8 枚コピペカード](docs/CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) - T658-extend
- [6/2 社長プレゼン 最終レビュー チェックリスト](docs/CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) - T663 deliverable
- [Sheets 追加タブ スキーマ (課題管理表 / QA 表)](docs/SHEETS_TRACKERS_SCHEMA.md)
- [開発ナレッジ連携フロー手順書](docs/DEVELOPMENT_KNOWLEDGE_FLOW.md)
- [6/2 社長デモ向け 連携実施証跡](docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md)
- [プロジェクト構成方針](docs/PROJECT_STRUCTURE.md)
- [WBS 同期ガイド](docs/WBS_SYNC_GUIDE.md)
