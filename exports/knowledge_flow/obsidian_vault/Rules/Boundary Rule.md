# Boundary Rule: Personal Notes vs Official Docs

This rule establishes a strict boundary to distinguish between local developer thoughts/notes and official project repositories.

## 1. Local Developer Vault (Obsidian)
- **Scope:** Rough designs, unreviewed prompts, personal meeting notes, personal ideas, experimental settings.
- **Audience:** Individual developer or private development session.
- **Rule:** May contain rough language, unchecked hypotheses, and raw logs. Strictly gitignored from the production repository (under `exports/knowledge_flow/obsidian_vault` for demo purposes only).

## 2. Official Documentation (docs/)
- **Scope:** Design decisions (ADR), approved specifications, setup guides, WBS schedules, and target roadmaps.
- **Audience:** CEO, Stakeholders, full dev team.
- **Rule:** Must be clean, verified, and free of any credentials or private data. Updated exclusively via intentional git commits to the `docs/` directory.

## 3. Promotion Process
When a design, prompt, or architectural plan transitions from experimental to official:
1. Refine the note to be descriptive, clean, and complete.
2. Port it to the appropriate file under the [docs/](file:///docs/) directory.
3. Update [docs/WBS.md](file:///docs/WBS.md) and [data/WBS.tsv](file:///data/WBS.tsv) to sync schedules and deliverables.
4. Commit intentionally and push.
