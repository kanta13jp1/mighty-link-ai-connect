#!/usr/bin/env python3
"""Generate rich HTML Markdown and Mermaid viewers for docs and sequence diagrams."""

from pathlib import Path
import re

# 1. Create docs/DEVELOPMENT_KNOWLEDGE_FLOW.html
doc_source = Path("docs/DEVELOPMENT_KNOWLEDGE_FLOW.md").read_text(encoding="utf-8")
doc_source_escaped = doc_source.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>開発ナレッジ連携フロー手順書 — Mighty Skill-Bridge</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown-dark.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        .topbar {{
            position: sticky;
            top: 0;
            background: rgba(13, 17, 23, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }}
        .back-link {{
            color: #8bdcff;
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px 24px;
            background-color: transparent !important;
        }}
    </style>
</head>
<body>
    <header class="topbar">
        <a href="../../index.html" class="back-link">← ホームに戻る</a>
        <span style="font-size: 12px; color: #8b949e;">Mighty Skill-Bridge ナレッジベース</span>
    </header>
    <article class="markdown-body" id="content">
        <!-- Rendered by Marked.js -->
    </article>
    <script>
        const rawMarkdown = `{doc_source_escaped}`;
        document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
    </script>
</body>
</html>
"""

Path("docs/DEVELOPMENT_KNOWLEDGE_FLOW.html").write_text(html_content, encoding="utf-8")
print("[1] docs/DEVELOPMENT_KNOWLEDGE_FLOW.html generated successfully!")

# 2. Fix exports/sequence-diagrams/index.html to use robust multi-CDN for Mermaid and local fallback
seq_path = Path("exports/sequence-diagrams/index.html")
seq_content = seq_path.read_text(encoding="utf-8")

# Update 'ホームに戻る' link to point cleanly to root
seq_content = seq_content.replace('href="../../"', 'href="../../index.html"')
seq_content = seq_content.replace('href="../../"', 'href="../../index.html"')

# Add robust Mermaid CDN with auto-rendering
mermaid_script = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose'
    });
  } else {
    // Fallback load from cdnjs
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.4.1/mermaid.min.js';
    s.onload = function() {
      mermaid.initialize({ startOnLoad: true, theme: 'dark' });
    };
    document.head.appendChild(s);
  }
</script>
"""

seq_content = re.sub(r'<script src="https://unpkg.com/mermaid@11/dist/mermaid.min.js"></script>[\s\S]*?</script>', mermaid_script.strip(), seq_content)
seq_path.write_text(seq_content, encoding="utf-8")
print("[2] exports/sequence-diagrams/index.html updated with robust Mermaid renderer!")
