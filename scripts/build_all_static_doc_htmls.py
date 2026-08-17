#!/usr/bin/env python3
"""Pre-render all docs/*.md and docs/training/*.md to static HTML with Marked.js & Mermaid.js."""

from pathlib import Path
import json
import html

DOCS_DIR = Path("docs")

template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Mighty-Link Documentation</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown-dark.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0b0f19;
            color: #e2e8f0;
            padding: 32px 20px;
            margin: 0;
        }}
        .doc-container {{
            max-width: 980px;
            margin: 0 auto;
            background: #131b2e;
            padding: 40px;
            border-radius: 16px;
            border: 1px solid #1e293b;
            box-shadow: 0 12px 36px rgba(0,0,0,0.5);
        }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 24px;
            color: #8bdcff;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        .markdown-body {{
            background-color: transparent !important;
            color: #e2e8f0 !important;
            font-size: 15px;
            line-height: 1.7;
        }}
        .mermaid {{
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="doc-container">
        <a href="../../index.html" class="back-link">← ホームに戻る</a>
        <article class="markdown-body" id="rendered-doc"></article>
    </div>
    <script>
        const rawMarkdown = {json_content};
        document.getElementById('rendered-doc').innerHTML = marked.parse(rawMarkdown);

        // Render Mermaid code blocks
        document.querySelectorAll('pre code.language-mermaid').forEach((block) => {{
            const pre = block.parentElement;
            const div = document.createElement('div');
            div.className = 'mermaid';
            div.textContent = block.textContent;
            pre.parentNode.replaceChild(div, pre);
        }});

        if (typeof mermaid !== 'undefined') {{
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'dark',
                securityLevel: 'loose'
            }});
            mermaid.run();
        }}
    </script>
</body>
</html>"""

count = 0
for md_file in DOCS_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    title = html.escape(md_file.stem)
    json_content = json.dumps(content)
    
    html_output = template.format(
        title=title,
        json_content=json_content
    )
    
    html_path = md_file.with_suffix(".html")
    html_path.write_text(html_output, encoding="utf-8")
    count += 1

print(f"[SUCCESS] Built {count} static HTML documents across docs/!")
