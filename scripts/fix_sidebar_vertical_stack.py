#!/usr/bin/env python3
"""Fix sidebar vertical layout, remove duplicate footer links, and ensure flawless UI/UX."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Enforce strict vertical column layout for sidebar nav links
sidebar_vertical_css = """
        /* Strict Vertical Column for Global Sidebar Navigation */
        .global-app-sidebar .nav-links {
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            justify-content: flex-start !important;
            gap: 6px !important;
            width: 100% !important;
            border-top: none !important;
            padding: 0 !important;
            overflow: visible !important;
        }

        .global-app-sidebar .sidebar-nav-item {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-start !important;
            width: 100% !important;
            box-sizing: border-box !important;
            padding: 10px 14px !important;
            border-radius: 8px !important;
            color: var(--muted) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            text-decoration: none !important;
            border: 1px solid transparent !important;
            white-space: nowrap !important;
            transition: all 0.2s ease !important;
            cursor: pointer !important;
        }

        .global-app-sidebar .sidebar-nav-item:hover {
            background: rgba(255, 255, 255, 0.05) !important;
            color: #ffffff !important;
            transform: translateX(3px) !important;
        }

        .global-app-sidebar .sidebar-nav-item.active {
            background: rgba(186, 255, 102, 0.12) !important;
            border: 1px solid rgba(186, 255, 102, 0.4) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
        }
"""

if "Strict Vertical Column for Global Sidebar Navigation" not in content:
    content = content.replace("</style>", sidebar_vertical_css + "\n    </style>")

# 2. Clean up Footer Navigation Redundancy (Replace duplicate links with Architecture & Compliance links)
footer_redundant_pattern = r'<div class="footer-col">\s*<h4>製品・機能</h4>[\s\S]*?</div>\s*</div>'
clean_footer_col = """<div class="footer-col">
                        <h4>サービス情報</h4>
                        <div class="footer-links">
                            <a href="#video-section" onclick="switchAppTab('home-view', true)">AI Brand Video</a>
                            <a href="#models" onclick="switchAppTab('home-view', true)">搭載モデル一覧</a>
                            <a href="#knowledge-flow-demo" onclick="switchAppTab('home-view', true)">アーキテクチャ図</a>
                            <a href="docs/training/ADMIN_MANAGEMENT_TRAINING_HANDBOOK.md" target="_blank" rel="noopener">管理者マニュアル</a>
                        </div>
                    </div>"""

content = re.sub(footer_redundant_pattern, clean_footer_col, content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Sidebar vertical stack enforced and footer redundancy eliminated!")
