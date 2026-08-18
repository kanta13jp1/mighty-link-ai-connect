#!/usr/bin/env python3
"""Remove all remaining #training-modal checks and internal target="_blank" from index.html."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Remove #training-modal in click listener
content = content.replace("!href.startsWith('#training-modal')", "true")
content = content.replace(" && true", "")

# 2. Remove target="_blank" and rel="noopener" from internal links (knowledge_flow, admin, etc.)
# Replace internal artifact links
content = content.replace('href="admin" style="color: var(--blue); font-weight: 700; text-decoration: underline;" target="_blank" rel="noopener"', 'href="admin" style="color: var(--blue); font-weight: 700; text-decoration: underline;"')
content = content.replace('href="exports/knowledge_flow/notebooklm_agent_brief.md" target="_blank" rel="noopener"', 'href="exports/knowledge_flow/notebooklm_agent_brief.md"')
content = content.replace('href="exports/knowledge_flow/slack_ceo_update.md" target="_blank" rel="noopener"', 'href="exports/knowledge_flow/slack_ceo_update.md"')
content = content.replace('href="exports/knowledge_flow/notion_decision_log.csv" target="_blank" rel="noopener"', 'href="exports/knowledge_flow/notion_decision_log.csv"')
content = content.replace('href="exports/knowledge_flow/obsidian_vault/Mighty%20Skill-Bridge%20Home.md" target="_blank" rel="noopener"', 'href="exports/knowledge_flow/obsidian_vault/Mighty%20Skill-Bridge%20Home.md"')
content = content.replace('href="admin" target="_blank" rel="noopener">管理者画面 (DB直通)', 'href="admin">管理者画面 (DB直通)')
content = content.replace('map(path => `<a href="${path}" target="_blank" rel="noopener">${path}</a>`)', 'map(path => `<a href="${path}">${path}</a>`)')

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] All internal target='_blank' and #training-modal references cleaned!")
