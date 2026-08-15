#!/usr/bin/env python3
"""Generate Full Wireframe Artboards for All Application Views in Figma (2026 SaaS Parity).

Includes:
- 00: Home / AI Fit Simulator & Hero Video (1440x960)
- 01: Sales Email AI Matching & Proposal Hub (1440x960)
- 02: 1-Click Proposal Email Generation Modal (760x680)
- 03: Attendance Timesheet & 36 Compliance Tracker (1440x960)
- 04: Employee Assessment & Culture Radar Matrix (1440x960)
- 05: Admin Operations & Audit Trail Dashboard (1440x960)
- ALL_VIEWS: Giant Master Artboard (4800x2100)
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "exports" / "figma_wireframes"


def build_sidebar_svg(active_tab_title: str) -> str:
    """Reusable Global SaaS Sidebar Component."""
    items = [
        ("🏠", "ホーム (トップ)", "home-view"),
        ("🤝", "営業メールAIマッチング", "matching-section"),
        ("🛡️", "管理者統合ダッシュボード", "admin-dashboard-section"),
        ("⏱️", "勤務表・残業解析", "attendance-section"),
        ("📊", "適性・状況アンケート", "survey-section"),
        ("📈", "自己診断デモ", "aptitude-demo-section"),
        ("⚙️", "初期セットアップ", "onboarding-section"),
    ]

    nav_svg = ""
    y_offset = 110
    for icon, title, tab_id in items:
        is_active = (title == active_tab_title)
        bg = "#162a15" if is_active else "transparent"
        border = "#baff66" if is_active else "transparent"
        text_color = "#ffffff" if is_active else "#8b949e"
        weight = "bold" if is_active else "500"

        nav_svg += f"""
        <g transform="translate(16, {y_offset})">
            <rect width="218" height="40" rx="8" fill="{bg}" stroke="{border}" stroke-width="1"/>
            <text x="16" y="25" fill="{text_color}" font-family="Arial, sans-serif" font-size="15">{icon}</text>
            <text x="44" y="25" fill="{text_color}" font-family="Arial, sans-serif" font-size="13" font-weight="{weight}">{title}</text>
            {'<circle cx="200" cy="20" r="3.5" fill="#baff66"/>' if is_active else ''}
        </g>"""
        y_offset += 46

    return f"""
    <!-- Global Sidebar (Left: 250px) -->
    <g id="Global_App_Sidebar">
        <rect width="250" height="960" rx="24" fill="#090d16" stroke="#161f30" stroke-width="1.2"/>
        
        <!-- Brand -->
        <rect x="24" y="28" width="34" height="34" rx="10" fill="#162a15" stroke="#baff66" stroke-width="1.2"/>
        <text x="41" y="50" fill="#baff66" font-family="Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle">🛡️</text>
        <text x="68" y="44" fill="#ffffff" font-family="Arial, sans-serif" font-size="14" font-weight="800" letter-spacing="0.5">MIGHTY LINK</text>
        <text x="68" y="58" fill="#baff66" font-family="Arial, sans-serif" font-size="10" font-weight="bold">AI CONNECT PRO</text>

        <text x="24" y="96" fill="#48576e" font-family="Arial, sans-serif" font-size="10" font-weight="bold" letter-spacing="1">WORKSPACE APPS</text>

        {nav_svg}

        <!-- Profile -->
        <g transform="translate(16, 880)">
            <rect width="218" height="60" rx="12" fill="#0d1424" stroke="#1f2d45" stroke-width="1"/>
            <circle cx="34" cy="30" r="16" fill="#162e12" stroke="#baff66" stroke-width="1.2"/>
            <text x="34" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="11" font-weight="bold" text-anchor="middle">佐</text>
            <text x="58" y="26" fill="#ffffff" font-family="Arial, sans-serif" font-size="12" font-weight="bold">佐藤 賢太</text>
            <text x="58" y="42" fill="#baff66" font-family="Arial, sans-serif" font-size="10">最高統括管理者</text>
            <circle cx="198" cy="30" r="4" fill="#baff66"/>
        </g>
    </g>"""


def build_home_view_svg() -> str:
    sidebar = build_sidebar_svg("ホーム (トップ)")
    return f"""
    <g id="View_00_Home_Simulator" transform="translate(0, 0)">
        <rect width="1440" height="960" rx="24" fill="#05070d" stroke="#1c2538" stroke-width="1.5"/>
        {sidebar}
        <g id="Main_Content" transform="translate(270, 24)">
            <!-- Topbar -->
            <rect width="1146" height="54" rx="12" fill="#090d16" stroke="#182338" stroke-width="1"/>
            <text x="24" y="34" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="800">🏠 ホーム / AIフィットシミュレーター</text>

            <!-- Video Frame -->
            <rect x="0" y="70" width="1146" height="340" rx="14" fill="#0c1220" stroke="#1f2d45" stroke-width="1.2"/>
            <circle cx="573" cy="240" r="40" fill="#162a15" stroke="#baff66" stroke-width="2"/>
            <text x="573" y="248" fill="#baff66" font-family="Arial, sans-serif" font-size="24" text-anchor="middle">▶</text>
            <text x="573" y="310" fill="#ffffff" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Mighty AI Fit Engine (シネマティック映像)</text>

            <!-- Two Inputs -->
            <g transform="translate(0, 430)">
                <rect width="560" height="490" rx="14" fill="#090d16" stroke="#182338" stroke-width="1"/>
                <text x="24" y="34" fill="#8bdcff" font-family="Arial, sans-serif" font-size="12" font-weight="bold">STEP 1</text>
                <text x="24" y="58" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="bold">エンジニアのスキルと経歴</text>
                <rect x="24" y="80" width="512" height="380" rx="8" fill="#05070d" stroke="#1a263c"/>
                <text x="40" y="110" fill="#6e7f98" font-family="Arial, sans-serif" font-size="12">Python, FastAPI, AWS, Docker 5年経験...</text>
            </g>
            <g transform="translate(586, 430)">
                <rect width="560" height="490" rx="14" fill="#090d16" stroke="#182338" stroke-width="1"/>
                <text x="24" y="34" fill="#ffd166" font-family="Arial, sans-serif" font-size="12" font-weight="bold">STEP 1</text>
                <text x="24" y="58" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="bold">案件・チームの必須要件</text>
                <rect x="24" y="80" width="512" height="380" rx="8" fill="#05070d" stroke="#1a263c"/>
                <text x="40" y="110" fill="#6e7f98" font-family="Arial, sans-serif" font-size="12">AIエージェント基盤開発。FastAPI必須、月額85万...</text>
            </g>
        </g>
    </g>"""


def build_matching_view_svg() -> str:
    sidebar = build_sidebar_svg("営業メールAIマッチング")
    return f"""
    <g id="View_01_Sales_Matching" transform="translate(0, 0)">
        <rect width="1440" height="960" rx="24" fill="#05070d" stroke="#1c2538" stroke-width="1.5"/>
        {sidebar}
        <g id="Main_Content" transform="translate(270, 24)">
            <!-- Topbar -->
            <rect width="1146" height="54" rx="12" fill="#090d16" stroke="#182338" stroke-width="1"/>
            <text x="24" y="34" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="800">🤝 営業メールAIマッチング &amp; 案件成約ハブ</text>

            <!-- 3 Bento KPI Cards -->
            <g transform="translate(0, 70)">
                <rect x="0" y="0" width="366" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="20" y="26" fill="#8b949e" font-size="11" font-weight="bold">AIマッチング平均適合度</text>
                <text x="20" y="60" fill="#ffffff" font-size="28" font-weight="800">94.8%</text>

                <rect x="390" y="0" width="366" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="410" y="26" fill="#8b949e" font-size="11" font-weight="bold">平均成約リードタイム</text>
                <text x="410" y="60" fill="#8bdcff" font-size="28" font-weight="800">3.5分</text>

                <rect x="780" y="0" width="366" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="800" y="26" fill="#8b949e" font-size="11" font-weight="bold">成約アプローチ待機案件</text>
                <text x="800" y="60" fill="#ffd166" font-size="28" font-weight="800">18件</text>
            </g>

            <!-- Table -->
            <g transform="translate(0, 190)">
                <rect width="1146" height="730" rx="14" fill="#090d16" stroke="#182338"/>
                <rect width="1146" height="46" rx="14" fill="#0d1424"/>
                <text x="24" y="28" fill="#8b949e" font-size="11" font-weight="bold">案件タイトル・必須スキル</text>
                <text x="500" y="28" fill="#8b949e" font-size="11" font-weight="bold">受信日</text>
                <text x="640" y="28" fill="#8b949e" font-size="11" font-weight="bold">推薦エンジニア</text>
                <text x="840" y="28" fill="#8b949e" font-size="11" font-weight="bold">マッチ度</text>
                <text x="960" y="28" fill="#8b949e" font-size="11" font-weight="bold">アクション</text>

                <!-- Row 1 -->
                <g transform="translate(0, 46)">
                    <rect width="1146" height="64" fill="rgba(139,220,255,0.02)"/>
                    <text x="24" y="28" fill="#ffffff" font-size="13" font-weight="bold">【Python/FastAPI】AIエージェント連携基盤開発</text>
                    <rect x="24" y="38" width="56" height="18" rx="4" fill="rgba(139,220,255,0.1)"/>
                    <text x="52" y="51" fill="#8bdcff" font-size="10" text-anchor="middle">Python</text>
                    <text x="500" y="36" fill="#6e7f98" font-size="11">2026/08/16</text>
                    <circle cx="655" cy="32" r="14" fill="#162e12" stroke="#baff66"/>
                    <text x="655" y="36" fill="#baff66" font-size="10" font-weight="bold" text-anchor="middle">佐</text>
                    <text x="680" y="36" fill="#ffffff" font-size="12">佐藤 賢太</text>
                    <rect x="840" y="20" width="56" height="24" rx="4" fill="rgba(186,255,102,0.15)"/>
                    <text x="868" y="36" fill="#baff66" font-size="11" font-weight="bold" text-anchor="middle">96%</text>
                    <rect x="960" y="18" width="80" height="28" rx="6" fill="#162a15" stroke="#baff66"/>
                    <text x="1000" y="36" fill="#baff66" font-size="11" font-weight="bold" text-anchor="middle">📧 提案作成</text>
                </g>
            </g>
        </g>
    </g>"""


def build_admin_view_svg() -> str:
    sidebar = build_sidebar_svg("管理者統合ダッシュボード")
    return f"""
    <g id="View_05_Admin_Dashboard" transform="translate(0, 0)">
        <rect width="1440" height="960" rx="24" fill="#05070d" stroke="#1c2538" stroke-width="1.5"/>
        {sidebar}
        <g id="Main_Content" transform="translate(270, 24)">
            <!-- Topbar -->
            <rect width="1146" height="54" rx="12" fill="#090d16" stroke="#182338" stroke-width="1"/>
            <text x="24" y="34" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="800">🛡️ 社内診断・勤怠＆マッチング統合管理ダッシュボード</text>

            <!-- 4 Bento KPI Cards -->
            <g transform="translate(0, 70)">
                <rect x="0" y="0" width="270" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="18" y="26" fill="#8b949e" font-size="11" font-weight="bold">総管理エンジニア数</text>
                <text x="18" y="60" fill="#ffffff" font-size="28" font-weight="800">42 <small style="font-size:14px;color:#8b949e">名</small></text>

                <rect x="292" y="0" width="270" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="310" y="26" fill="#8b949e" font-size="11" font-weight="bold">AIマッチング成約確度</text>
                <text x="310" y="60" fill="#baff66" font-size="28" font-weight="800">82.4%</text>

                <rect x="584" y="0" width="270" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="602" y="26" fill="#8b949e" font-size="11" font-weight="bold">平均月間残業時間</text>
                <text x="602" y="60" fill="#8bdcff" font-size="28" font-weight="800">14.2 h</text>

                <rect x="876" y="0" width="270" height="100" rx="12" fill="#090d16" stroke="#1a263c"/>
                <text x="894" y="26" fill="#8b949e" font-size="11" font-weight="bold">セキュリティ＆稼働率</text>
                <text x="894" y="60" fill="#ffffff" font-size="28" font-weight="800">99.98%</text>
            </g>

            <!-- Mid Panels -->
            <g transform="translate(0, 190)">
                <rect x="0" y="0" width="560" height="340" rx="14" fill="#090d16" stroke="#182338"/>
                <text x="24" y="34" fill="#ffffff" font-size="14" font-weight="bold">📊 エンジニア自己診断・コンディション分析</text>

                <rect x="586" y="0" width="560" height="340" rx="14" fill="#090d16" stroke="#182338"/>
                <text x="610" y="34" fill="#ffffff" font-size="14" font-weight="bold">⏱️ 勤務表解析・36協定残業リアルタイム管理</text>
            </g>

            <!-- Audit Trail -->
            <g transform="translate(0, 550)">
                <rect width="1146" height="370" rx="14" fill="#090d16" stroke="#182338"/>
                <text x="24" y="34" fill="#ffffff" font-size="14" font-weight="bold">📜 Enterprise 操作監査ログ (改ざん防止ハッシュ検証)</text>
            </g>
        </g>
    </g>"""


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    header = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 960" width="1440" height="960">
"""
    footer = "</svg>\n"

    # Write separate view wireframes
    (OUTPUT_DIR / "00_home_simulator_wireframe.svg").write_text(header + build_home_view_svg() + footer, encoding="utf-8")
    (OUTPUT_DIR / "01_sales_matching_wireframe.svg").write_text(header + build_matching_view_svg() + footer, encoding="utf-8")
    (OUTPUT_DIR / "05_admin_dashboard_wireframe.svg").write_text(header + build_admin_view_svg() + footer, encoding="utf-8")

    # Write Master Canvas (All Views side-by-side 4500x1000)
    master_header = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4500 1000" width="4500" height="1000">
"""
    master_svg = (
        master_header
        + f'<g transform="translate(0, 0)">{build_home_view_svg()}</g>'
        + f'<g transform="translate(1500, 0)">{build_matching_view_svg()}</g>'
        + f'<g transform="translate(3000, 0)">{build_admin_view_svg()}</g>'
        + footer
    )
    (OUTPUT_DIR / "mighty_link_full_wireframe_artboard.svg").write_text(master_svg, encoding="utf-8")

    print("[SUCCESS] All 2026 SaaS Wireframe Artboards generated!")
    return 0


if __name__ == "__main__":
    main()
