---
name: third-party-code-review
description: Execute rigorous third-party code review, architectural sanity checks, KISS/YAGNI verification, and documentation divergence checks following Claude Code standards.
triggers:
  - "review code"
  - "third party review"
  - "code review"
  - "verify architecture"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# Third-Party Code Review & Quality Assurance Skill

This skill enforces independent, rigorous third-party code reviews on modified files and git diffs before merging or committing. It evaluates code quality, security, performance, KISS/YAGNI principles, and doc synchronization.

---

## 1. Review Checklist & Evaluation Criteria

| Category | Review Points & Verification Criteria |
| :--- | :--- |
| **1. KISS & YAGNI** | Are there unnecessary abstractions, overly complex generics, or premature optimizations? Is the solution the simplest direct implementation? |
| **2. Security & Secrets** | Are any API keys, tokens, OAuth secrets, or credentials exposed? Are SQL queries parameterized against injection? |
| **3. Type Safety** | Are TypeScript / Python types strict? Are `any` or untyped dictionaries avoided for core domain models? |
| **4. Existing Code Respect** | Did the changes inadvertently delete, modify, or corrupt unrelated comments, docstrings, or surrounding logic? |
| **5. Docs Divergence** | Are changes reflected in `docs/` and `data/WBS.tsv`? Did the change introduce undocumented breaking changes? |
| **6. E2E Link & Endpoint Reachability** | Do all `<a href="...">` links point to real, routed, and mounted endpoints that return HTTP 200? Never rely solely on static string presence checks; verify actual HTTP reachability and browser renderability (preventing 404 Not Found on raw `.md` links). |

---

## 2. Execution Runbook (PowerShell)

### Step 1: Inspect Working Tree & Diff
```powershell
# Review unstaged & staged changes
git status --short
git diff --stat
```

### Step 2: Run Full Automated Integrity & Test Suite
```powershell
python scripts/run_lane_preflight.py --full
```

### Step 3: Check Sensitive Files & Credentials
Verify no credential files are tracked or modified:
```powershell
git status --porcelain | Select-String -Pattern "credentials\.json|client_secret\.json|authorized_user\.json|\.env$"
```

---

## 3. Review Verdict Matrix

Format review findings in a structured Markdown table:

```markdown
### 📋 Code Review Summary

- **Verdict**: [APPROVE / REQUEST_CHANGES / COMMENT]
- **Target Files**: [file1.py](file:///...), [file2.ts](file:///...)

#### Findings & Action Items
1. **[CRITICAL / MAJOR / MINOR]**: Description of issue + Concrete suggested fix with code diff.
2. **KISS/YAGNI Evaluation**: Passed / Recommendations.
3. **Preflight Status**: Passed (0 errors).
```
