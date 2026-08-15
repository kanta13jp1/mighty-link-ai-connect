#!/usr/bin/env python3
"""Precisely wrap home view elements in <div id="home-view" class="app-tab-view home-tab-element">."""

from pathlib import Path

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Insert opening <div id="home-view" class="app-tab-view home-tab-element"> before hero section
target_hero = '<main id="top" tabindex="-1">\n        <!-- ==========================================================================\n             Step 1: AI Fit Simulation Profile Inputs (プロフィール入力)\n             ========================================================================== -->\n        <section class="hero"'
replacement_hero = '<main id="top" tabindex="-1">\n        <!-- ==========================================================================\n             HOME TAB VIEW (Landing Page & Fit Simulator)\n             ========================================================================== -->\n        <div id="home-view" class="app-tab-view home-tab-element">\n            <!-- ==========================================================================\n                 Step 1: AI Fit Simulation Profile Inputs (プロフィール入力)\n                 ========================================================================== -->\n            <section class="hero"'

if target_hero in content:
    content = content.replace(target_hero, replacement_hero, 1)
    print("[1] Opening #home-view inserted!")
else:
    # Try CRLF
    target_hero_crlf = target_hero.replace('\n', '\r\n')
    replacement_hero_crlf = replacement_hero.replace('\n', '\r\n')
    if target_hero_crlf in content:
        content = content.replace(target_hero_crlf, replacement_hero_crlf, 1)
        print("[1] Opening #home-view inserted (CRLF)!")
    else:
        print("[-] Target hero not found!")

# 2. Insert closing </div> before onboarding-section
target_onboarding = '        <!-- ==========================================================================\n             Step 0: 初期セットアップ / アクティベーション ウィザード (T752)'
replacement_onboarding = '        </div> <!-- end #home-view -->\n\n        <!-- ==========================================================================\n             Step 0: 初期セットアップ / アクティベーション ウィザード (T752)'

if target_onboarding in content:
    content = content.replace(target_onboarding, replacement_onboarding, 1)
    print("[2] Closing #home-view inserted!")
else:
    target_onboarding_crlf = target_onboarding.replace('\n', '\r\n')
    replacement_onboarding_crlf = replacement_onboarding.replace('\n', '\r\n')
    if target_onboarding_crlf in content:
        content = content.replace(target_onboarding_crlf, replacement_onboarding_crlf, 1)
        print("[2] Closing #home-view inserted (CRLF)!")
    else:
        print("[-] Target onboarding not found!")

# 3. Also wrap bottom sections (#models, #knowledge-flow-demo, #support) in home-view or give them home-tab-element class
content = content.replace(
    '<section id="models" class="model-band fade-in-on-scroll"',
    '<section id="models" class="app-tab-view home-tab-element model-band fade-in-on-scroll"'
)
content = content.replace(
    '<section id="knowledge-flow-demo" class="knowledge-flow-section fade-in-on-scroll"',
    '<section id="knowledge-flow-demo" class="app-tab-view home-tab-element knowledge-flow-section fade-in-on-scroll"'
)
content = content.replace(
    '<section class="support-section fade-in-on-scroll" id="support"',
    '<section class="app-tab-view home-tab-element support-section fade-in-on-scroll" id="support"'
)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] index.html successfully structured for Tabbed SPA!")
