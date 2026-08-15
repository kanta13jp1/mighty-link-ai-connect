---
name: e2e-link-auditor
description: Audit and verify all internal, external, header, footer, and navigation links for HTTP 200 reachability and valid HTML rendering, preventing 404 Not Found errors on raw markdown or unmounted routes.
triggers:
  - "check links"
  - "audit links"
  - "broken link"
  - "verify link reachability"
  - "link review"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# E2E Link & Endpoint Reachability Auditor Skill

This skill enforces thorough verification of all interactive links (`<a href="...">`) within the application to prevent 404 Not Found regressions, unmounted static paths, and broken relative links.

---

## 1. Core Verification Principles

1. **Never rely on static string matching**: Checking `assert "docs/TERMS_OF_SERVICE.md" in html` is insufficient. The endpoint must actually be reachable via HTTP.
2. **Verify Server Routing & Static Mounts**: Any link pointing to `/docs/...`, `/exports/...`, or `/admin/...` must be explicitly handled by the backend server (`src/app.py`) and return `200 OK`.
3. **Format & Browser Compatibility**: Raw `.md` files should be served with appropriate content-type or rendered via a clean HTML viewer for standard browser display.

---

## 2. Automated Runbook (PowerShell)

### Step 1: Run Broken Link Audit Test
```powershell
python -m pytest tests/test_footer_and_nav_links.py -v
```

### Step 2: Full Preflight Integration
```powershell
python scripts/run_lane_preflight.py
```
