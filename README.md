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
- [6/2 社長プレゼン Canva / Figma リデザイン手順 + 8 枚コピペカード](docs/CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) - T658-extend (手動版)
- [Canva / Figma MCP セットアップ + 自動化フロー](docs/MCP_CANVA_FIGMA_SETUP_GUIDE_2026-06-02.md) - T658-mcp-extend (自動化版、推奨)
- [Figma Slides: Mighty Skill-Bridge CEO Brief 2026-06-02](https://www.figma.com/slides/PAQWzAUPoPTy3ibLcOmPDC) - 2026-05-24 Figma MCP で 9 slides 自動生成、当日プレゼン用第一候補
- [Branded PPTX on Drive: CEO Presentation Deck 2026-06-02 (Branded)](https://docs.google.com/presentation/d/1myH1m8TKiukdxR7F_EertJ1102CfglBC/edit?usp=drivesdk) - 2026-05-24 アップロード、PowerPoint フォールバック
- [UI Wireframes — Live Catalog (10 動くプロト)](exports/wireframes/index.html) - 2026-05-24 materialize、ローカル `python src/app.py` 起動後 `http://localhost:8000/exports/wireframes/` で 10 WF をブラウザ確認可能
- [UI Wireframes — Implementation-Ready Spec Pack](docs/wireframes/README.md) - 2026-05-24 生成、10 WF を AI に渡して即実装できる spec md x10 + 機械可読 JSON。社長 6/2 判断後の AI 実装着手用
- [UI Wireframes — 10 Patterns (Canva, Branded — Drive)](https://docs.google.com/presentation/d/1JKu7tAw1h4BqXMAsF41qolbQPUKj8KLW/edit?usp=drivesdk) - 2026-05-24 Canva MCP 生成、cyber palette フルカラー版、社長判断材料の第一候補
- [UI Wireframes — 10 Patterns (Canva — edit)](https://www.canva.com/d/Mft5giDcMgir88Y) / [view](https://www.canva.com/d/lLCcnCJnbJE9Xsa) - Canva 上で 12 ページを編集可能
- [UI Wireframes — 10 Patterns (greyscale, Drive)](https://docs.google.com/presentation/d/1qTdOWsLhUf0GzVDkztiuuLczcYkQuQfo/edit?usp=drivesdk) - 2026-05-24 python-pptx 生成、印刷向け greyscale 版
- [UI Wireframes Companion (Figma file)](https://www.figma.com/design/aiQt3c1Cenru4x6GMcLuL5) - Figma 上で 10 パターンを編集可能 (MCP rate limit 解除後に同内容を流し込み予定)
- [6/2 社長プレゼン 最終レビュー チェックリスト](docs/CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) - T663 deliverable
- [Sheets 追加タブ スキーマ (課題管理表 / QA 表)](docs/SHEETS_TRACKERS_SCHEMA.md)
- [開発ナレッジ連携フロー手順書](docs/DEVELOPMENT_KNOWLEDGE_FLOW.md)
- [6/2 社長デモ向け 連携実施証跡](docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md)
- [プロジェクト構成方針](docs/PROJECT_STRUCTURE.md)
- [WBS 同期ガイド](docs/WBS_SYNC_GUIDE.md)
- [シーケンス図集 (Mermaid)](docs/SEQUENCE_DIAGRAMS.md) - 2026-05-26 新規。AI フィット診断 / Mock fallback / 3-tool 開発フロー / 採用 LP エントリー の 4 パターン
- [シーケンス図 HTML 版 (インタラクティブ)](exports/sequence-diagrams/index.html) - 同 4 図を Mermaid runtime で描画する HTML。公開デモから「Architecture」リンクで遷移
