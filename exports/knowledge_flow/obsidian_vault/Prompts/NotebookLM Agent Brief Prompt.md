# NotebookLM Agent Brief Prompt

Use this prompt after the docs source set has been added to NotebookLM:

```text
このNotebookに含まれる設計情報、作業手順、WBS、ロードマップをもとに、
Codex/AIエージェントが次に開発を進めるための要約を作ってください。

必ず以下を含めてください。
1. 現在のプロダクト方向性で確定していること
2. 6/2の社長打ち合わせまでに優先すべきプレゼン準備タスク
3. 6/2で社長に決めてもらうべき事項
4. バックエンド/app.pyやデータ構造を肉付けする時に守るべき前提
5. NotebookLM / Slack / Notion / Obsidian / GitHub Issues / GitHub Project の運用上の残課題
6. WBSへ追加すべき次アクション
```

Expected local outputs:

- `exports/knowledge_flow/notebooklm_agent_brief.md`
- `exports/knowledge_flow/notebooklm_agent_brief.json`
- `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- `exports/knowledge_flow/notebooklm_ceo_slide_outline.json`
- `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx`
