# AGENTS.md

## Project Operating Rules

- Read the relevant files under `docs/` before changing code or project data.
- At the start of every session, check the latest official documentation that applies to the work:
  - Anthropic Claude Code: `https://code.claude.com/docs/en/overview`, `https://code.claude.com/docs/en/memory`, `https://code.claude.com/docs/en/settings`, `https://code.claude.com/docs/en/security`
  - OpenAI Codex: `https://developers.openai.com/codex`, `https://developers.openai.com/codex/guides/agents-md`, `https://developers.openai.com/codex/learn/best-practices`, `https://developers.openai.com/codex/mcp`
  - Google Gemini / Workspace: `https://ai.google.dev/gemini-api/docs/models`, `https://ai.google.dev/gemini-api/docs/caching`, `https://developers.google.com/workspace/sheets/api/guides/batchupdate`
- Every development session must complete at least one WBS task and reflect it in `data/WBS.tsv` and `docs/WBS.md`.
- Delete or rewrite stale docs aggressively. Do not preserve outdated model names, obsolete issue ranges, resolved blockers, or old sync counts as current guidance.
- Use `k-umezawa@ml-mightylink.com` for Google OAuth. Run `python scripts/verify_google_workspace_account.py` when touching Google integrations.
- Keep `data/WBS.tsv` as the WBS source of truth. Keep `data/issues_tracker.tsv` and `data/qa_tracker.tsv` as the source of truth for the Sheets `課題管理表` and `QA表` tabs.
- Do not commit secrets or local OAuth files: `client_secret.json`, `credentials.json`, `authorized_user.json`, `.claude/settings.local.json`, or `CLAUDE.local.md`.

## Required Session Closeout

Run these before finishing a session that changes project behavior or docs:

```powershell
python scripts/generate_knowledge_flow_demo.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

If NotebookLM-facing docs changed, also run:

```powershell
python scripts/sync_docs_to_notebooklm.py
python scripts/generate_ceo_presentation_deck.py
python scripts/upload_notebooklm_docs_to_drive.py
```

After validation, commit intentionally, push `main`, and push `master` from `main` so GitHub Pages stays aligned with the CEO-shared public URL.

## Tool Lanes

- Antigravity + Gemini: frontend polish, multimodal demos, browser-agent checks, and post-quota visual refinement.
- VSCode + Codex: backend, sync scripts, GitHub CLI, Google Workspace automation, CI/public-demo guard, and WBS source edits.
- VSCode + Claude Code: documentation, review, triage, checklist maintenance, and third-party review of Codex/Antigravity changes.

## Public Demo Guard

The public demo URL is shared with the CEO. Do not ship UI changes without checking:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

If the guard fails, fix or revert only your own change before pushing.
