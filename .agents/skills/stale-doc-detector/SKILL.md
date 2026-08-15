---
name: stale-doc-detector
description: Detect, audit, and rewrite stale documentation, outdated model references, obsolete issue ranges, and resolved blockers across docs/ and data/.
triggers:
  - "check stale docs"
  - "audit documentation"
  - "clean stale docs"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# Stale Documentation Detector & Audit Skill

This skill enforces the project operating rule: **"Delete or rewrite stale docs aggressively."** It audits markdown documentation in `docs/` and data trackers to ensure outdated information is purged.

---

## 1. Stale Pattern Audit Matrix

Scan `docs/` and source files for known obsolete patterns:

| Obsolete Category | Stale Patterns to Flag & Remove | Replacement / Action |
| :--- | :--- | :--- |
| **Outdated Model Names** | `gpt-3.5-turbo`, `gemini-1.0`, `claude-2`, `claude-instant` | Upgrade to current official models (`Gemini 2.0 / 3.1 Pro`, `Claude 3.5 Sonnet / 3.7`, `GPT-4o`) |
| **Resolved Blockers** | Resolved blockers listed as active in `docs/` | Move to resolution history or remove from current guidance |
| **Obsolete Issue Ranges** | Old sync counts, stale issue ID ranges | Re-sync from `data/WBS.tsv` and `data/issues_tracker.tsv` |
| **Dead Links / Old URLs** | Legacy internal URLs, broken relative markdown paths | Fix file links to valid `file:///` paths or current URLs |

---

## 2. Automated Scan Script (PowerShell)

Search for common stale indicators across `docs/`:

```powershell
# Scan for legacy model names and placeholders
Get-ChildItem -Path ./docs -Recurse -Filter "*.md" | Select-String -Pattern "gpt-3\.5|gemini-1\.0|claude-2|TODO:|FIXME:"

# Check WBS sync consistency
python scripts/sync_wbs_to_github.py --dry-run
```

---

## 3. Remediation Protocol

1. **Delete Obsolete Sections**: Do NOT preserve legacy guidance "for historical reasons" inside living specification documents.
2. **Synchronize with Source of Truth**: Ensure `docs/WBS.md` strictly mirrors `data/WBS.tsv`.
3. **Verify Integrity**: Re-run lane preflight after updating docs:
   ```powershell
   python scripts/run_lane_preflight.py
   ```
