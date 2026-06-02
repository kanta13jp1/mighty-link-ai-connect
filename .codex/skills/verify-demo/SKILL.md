---
name: verify-demo
description: Validate and guard the public demo URL.
triggers:
  - "verify demo"
  - "guard public demo"
  - "check public demo"
---

# Verify Demo Skill

Use this skill when you need to check if the public demo URL (GitHub Pages) has correct UI elements, CTA buttons, and required markers, ensuring no regression before pushing changes.

## Execution Steps

Run the following command in the PowerShell terminal:

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

## Expectations

- Verification of elements inside `index.html` and the online Page.
- Success exit code (0) if all elements are correct, preventing broken landing page deployments.
