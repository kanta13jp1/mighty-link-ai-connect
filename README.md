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

## Documents

- [セットアップ・運用手順書](docs/SETUP_GUIDE.md)
- [Google Workspace 移行・共有作業手順書](docs/GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md)
- [Codex 継続作業メモ](docs/CODEX_CONTINUATION_NOTES.md)
- [Backend AI Pipeline 設計メモ](docs/BACKEND_AI_PIPELINE.md) - deterministic fallback と AI 監査ログ
- [6/2 社長打ち合わせ プレゼン準備ブリーフ](docs/CEO_PRESENTATION_PREP_2026-06-02.md)
- [プロジェクト構成方針](docs/PROJECT_STRUCTURE.md)
- [WBS 同期ガイド](docs/WBS_SYNC_GUIDE.md)
