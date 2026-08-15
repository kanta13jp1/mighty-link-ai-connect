---
name: e2e-link-auditor
description: Audit and verify all internal, external, header, footer, and navigation links for HTTP 200 reachability and valid HTML rendering, preventing 404 Not Found errors on raw markdown or unmounted routes.
triggers:
  - "audit links"
  - "check broken links"
  - "verify link reachability"
  - "crawl links"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# E2E Link & Endpoint Reachability Auditor Skill

This skill enforces strict link validation across all landing pages, HTML templates, and documentation links. It ensures no user clicks encounter HTTP 404 Not Found, broken anchors, or unrendered raw `.md` files.

---

## 1. Core Verification Directives

> [!IMPORTANT]
> **No Static Assumption Rule**: Never assume links work just because the href string matches a filename. All links (`<a href="...">`) must resolve to live HTTP endpoints returning status **200 OK** with valid `Content-Type: text/html` (or appropriate media type).

### Prohibited Patterns
- ❌ Links pointing to raw markdown files on static web servers (e.g. `href="docs/ARCHITECTURE.md"` resulting in browser download or 404).
- ❌ Fragment/anchor links pointing to non-existent `#id` targets.
- ❌ External links returning `404`, `403`, or `500`.

---

## 2. Automated Link Audit Script (PowerShell / Node.js)

Run the comprehensive link crawler against the target URL or local preview:

```powershell
# 1. Quick Python/Playwright Link Crawl
python -c "
import urllib.request
from bs4 import BeautifulSoup

url = 'https://kanta13jp1.github.io/mighty-link-ai-connect/'
req = urllib.request.urlopen(url)
soup = BeautifulSoup(req.read(), 'html.parser')
links = [a.get('href') for a in soup.find_all('a', href=True)]
print(f'Discovered {len(links)} links. Validating...')
for link in links:
    if link.startswith('http'):
        try:
            res = urllib.request.urlopen(link, timeout=5)
            print(f'[OK 200] {link}')
        except Exception as e:
            print(f'[ERROR] {link} -> {e}')
"
```

---

## 3. Remediations

1. **Raw Markdown Links**: Wrap documentation inside an interactive HTML modal, or route to GitHub/Docs viewer.
2. **Relative Route Links**: Ensure all SPA/Multi-page routes are mounted in `firebase.json` or GitHub Pages router.
3. **External Resources**: Verify all CDN scripts (Tailwind, Lucide, FontAwesome) load without CORS or 404 blocks.
