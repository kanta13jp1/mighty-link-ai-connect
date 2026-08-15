---
name: verify-demo
description: Validate and guard the public demo URL and UI components, ensuring all required elements, CTA buttons, and markers are functioning before pushing changes.
triggers:
  - "verify demo"
  - "guard public demo"
  - "check public demo"
  - "demo test"
license: Apache-2.0
metadata:
  version: v2
  publisher: mighty-link
---

# Verify Demo & Public Landing Page Skill

Use this skill when modifying frontend UI components, landing pages, or multimodal demo artifacts, ensuring no regression before committing or pushing changes.

---

## 1. Quick Verification Command (PowerShell)

Run the verification script against the production URL (`mightylink-app.com`) as well as the GitHub Pages fallback:
 
```powershell
# Live Production URL Verification (Mandatory after deploy)
python scripts/verify_public_demo.py --url https://mightylink-app.com/

# Public Demo Static Fallback Verification
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

---

## 2. Verification Checklist

The script checks for:
1. **HTTP Availability**: Valid 200 OK response with fast load time.
2. **Critical CTA Elements**:
   - `Hero CTA` buttons and interactive triggers.
   - External links (Docs, GitHub, Demo modals).
   - **Broken Link Audit**: All internal/external links in Header, Navigation, and Footer must return HTTP 200 without 404/500 errors.
3. **Multimodal Demo Markers**:
   - Knowledge Flow canvas / interactive SVG elements.
   - Presentation deck viewer / preview iframe.
4. **Layout & Responsiveness**:
   - Mobile viewport responsiveness and font rendering without clipping.

---

## 3. Failure Resolution & Remediation

If `verify_public_demo.py` exits with non-zero:
- **Element Missing**: Inspect `index.html` or the generated artifact in `firebase-hosting/` or GitHub Pages root.
- **Local Preview Test**: Launch local preview using Python HTTP server or `firebase emulators:start` before re-testing.
