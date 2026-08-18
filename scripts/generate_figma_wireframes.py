#!/usr/bin/env python3
"""Generate distinct, screen-specific wireframe SVGs for all application views in Figma.

Production-accurate UI/UX layouts:
- 00: Home / AI Fit Simulator & Hero Video (1440x960)
- 01: Sales Email AI Matching & Proposal Hub (1440x960)
- 02: Admin Operations & Audit Trail Dashboard (1440x960)
- 03: Attendance Timesheet & 36 Compliance Tracker (1440x960)
- 04: Employee Assessment & Survey Form (1440x960)
- 05: Aptitude Demo & Competency Map (1440x960)
- 06: Onboarding 3-Step Setup & Activation (1440x960)
- 07: Dedicated Training Guide 3-Course Curriculum (1440x960)
- 08: 1-Click Proposal Email Generation Modal (760x680)
- ALL_VIEWS: Master Artboard (6200x2200)
"""

from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "exports" / "figma_wireframes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_sidebar_svg(active_tab_title: str) -> str:
    """Reusable Global SaaS Sidebar Component (Vertical Stack)."""
    items = [
        ("🏠", "ホーム", "home-view"),
        ("🤝", "営業メールマッチング", "matching-section"),
        ("🛡️", "管理者ダッシュボード", "admin-dashboard-section"),
        ("⏱️", "勤怠管理", "attendance-section"),
        ("📊", "適性アンケート", "survey-section"),
        ("📈", "自己診断デモ", "aptitude-demo-section"),
        ("⚙️", "初期セットアップ", "onboarding-section"),
        ("📖", "研修ガイド", "training-section"),
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
        <text x="68" y="56" fill="#8b949e" font-family="Arial, sans-serif" font-size="10">AI CONNECT PORTAL</text>

        <!-- Navigation Links -->
        {nav_svg}

        <!-- Bottom User Card -->
        <g transform="translate(16, 880)">
            <rect width="218" height="56" rx="12" fill="#0d1424" stroke="#1e293b" stroke-width="1"/>
            <circle cx="34" cy="28" r="16" fill="#162e12" stroke="#baff66" stroke-width="1.2"/>
            <text x="34" y="33" fill="#baff66" font-family="Arial, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">佐</text>
            <text x="60" y="24" fill="#ffffff" font-family="Arial, sans-serif" font-size="12" font-weight="bold">佐藤 賢太</text>
            <text x="60" y="40" fill="#baff66" font-family="Arial, sans-serif" font-size="10">最高統括管理者</text>
            <circle cx="198" cy="28" r="4" fill="#baff66"/>
        </g>
    </g>"""


def get_screen_content(screen_key: str) -> str:
    """Generate distinct, screen-specific wireframe layouts."""
    if screen_key == "00_home":
        return """
        <!-- Home / AI Fit Simulator -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">AI スキル・カルチャー適合シミュレーター</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">即戦力性・カルチャー・成長性・定着率をリアルタイム多軸解析</text>
            
            <!-- Left: Profile Inputs (480px) -->
            <g transform="translate(0, 80)">
                <rect width="520" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">求職者・人材プロファイル入力</text>
                
                <rect x="24" y="55" width="472" height="40" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="80" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">経験職種: フルスタックエンジニア / 5年</text>
                
                <rect x="24" y="110" width="472" height="120" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="135" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">保有スキル: Python, TypeScript, React, GCP, Terraform</text>
                
                <rect x="24" y="245" width="472" height="40" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="270" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">希望年収: 750万〜900万円 / フルリモート</text>
                
                <rect x="24" y="300" width="472" height="340" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="330" fill="#baff66" font-family="Arial, sans-serif" font-size="13" font-weight="bold">候補者レーダーチャート &amp; AI適合レポート</text>
                <circle cx="260" cy="480" r="100" fill="none" stroke="#1e293b" stroke-dasharray="4"/>
                <polygon points="260,400 340,470 300,560 210,540 190,460" fill="rgba(186,255,102,0.15)" stroke="#baff66" stroke-width="2"/>
                
                <rect x="24" y="660" width="472" height="50" rx="10" fill="#162a15" stroke="#baff66"/>
                <text x="260" y="692" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle">⚡ 適合シミュレーションを実行</text>
            </g>
            
            <!-- Right: 4-Axis Score & Video (530px) -->
            <g transform="translate(540, 80)">
                <rect width="530" height="340" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold">4軸総合フィットスコア (94 / 100)</text>
                
                <g transform="translate(24, 60)">
                    <text x="0" y="15" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">即戦力性 (Performing-Fit)</text>
                    <rect x="200" y="5" width="280" height="12" rx="6" fill="#090d16"/>
                    <rect x="200" y="5" width="260" height="12" rx="6" fill="#baff66"/>
                    <text x="490" y="15" fill="#baff66" font-family="Arial, sans-serif" font-size="12" font-weight="bold">93%</text>
                </g>
                <g transform="translate(24, 95)">
                    <text x="0" y="15" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">カルチャー適合性 (Culture-Fit)</text>
                    <rect x="200" y="5" width="280" height="12" rx="6" fill="#090d16"/>
                    <rect x="200" y="5" width="250" height="12" rx="6" fill="#8bdcff"/>
                    <text x="490" y="15" fill="#8bdcff" font-family="Arial, sans-serif" font-size="12" font-weight="bold">89%</text>
                </g>
                <g transform="translate(24, 130)">
                    <text x="0" y="15" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">将来成長性 (Growth-Fit)</text>
                    <rect x="200" y="5" width="280" height="12" rx="6" fill="#090d16"/>
                    <rect x="200" y="5" width="270" height="12" rx="6" fill="#ffd166"/>
                    <text x="490" y="15" fill="#ffd166" font-family="Arial, sans-serif" font-size="12" font-weight="bold">96%</text>
                </g>
                <g transform="translate(24, 165)">
                    <text x="0" y="15" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">定着期待度 (Retention-Fit)</text>
                    <rect x="200" y="5" width="280" height="12" rx="6" fill="#090d16"/>
                    <rect x="200" y="5" width="265" height="12" rx="6" fill="#06d6a0"/>
                    <text x="490" y="15" fill="#06d6a0" font-family="Arial, sans-serif" font-size="12" font-weight="bold">95%</text>
                </g>

                <!-- Video Showcase Box -->
                <g transform="translate(0, 360)">
                    <rect width="530" height="380" rx="14" fill="#101726" stroke="#1e293b"/>
                    <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">サービス紹介デモビデオ</text>
                    <rect x="24" y="55" width="482" height="300" rx="10" fill="#000000" stroke="#1e293b"/>
                    <circle cx="265" cy="205" r="30" fill="rgba(186,255,102,0.2)" stroke="#baff66" stroke-width="2"/>
                    <polygon points="260,195 275,205 260,215" fill="#baff66"/>
                </g>
            </g>
        </g>"""

    elif screen_key == "01_matching":
        return """
        <!-- Sales Email AI Matching Hub -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">営業メール AIマッチング ＆ 提案ハブ</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">受信メールから案件要件を自動抽出し、最適人材を1-Clickで提案生成</text>
            
            <!-- Left: Incoming Sales Email Queue (480px) -->
            <g transform="translate(0, 80)">
                <rect width="500" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">📥 受信案件メール一覧 (新着 12件)</text>
                
                <!-- Email Item 1 (Selected) -->
                <g transform="translate(16, 55)">
                    <rect width="468" height="120" rx="10" fill="#162a15" stroke="#baff66" stroke-width="1.5"/>
                    <text x="20" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">【急募】FinTech向けPython/GCPリードエンジニア</text>
                    <text x="20" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">送信元: 株式会社サイバーソリューションズ / 10分前</text>
                    <rect x="20" y="70" width="80" height="24" rx="6" fill="#090d16"/>
                    <text x="32" y="86" fill="#baff66" font-family="Arial, sans-serif" font-size="11">単価 110万</text>
                    <rect x="110" y="70" width="90" height="24" rx="6" fill="#090d16"/>
                    <text x="120" y="86" fill="#8bdcff" font-family="Arial, sans-serif" font-size="11">フルリモート</text>
                </g>
                
                <!-- Email Item 2 -->
                <g transform="translate(16, 190)">
                    <rect width="468" height="120" rx="10" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">AWS/Kubernetes インフラ刷新プロジェクト</text>
                    <text x="20" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">送信元: クラウドネイティブ株式会社 / 1時間前</text>
                </g>

                <!-- Email Item 3 -->
                <g transform="translate(16, 325)">
                    <rect width="468" height="120" rx="10" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Next.js/React フロントエンド開発リード</text>
                    <text x="20" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">送信元: グロースハック合同会社 / 3時間前</text>
                </g>
            </g>

            <!-- Right: Matched Candidates & 1-Click Proposal (550px) -->
            <g transform="translate(520, 80)">
                <rect width="550" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold">⚡ 最適適合人材 (マッチ度 96%)</text>
                
                <!-- Candidate Card -->
                <g transform="translate(20, 55)">
                    <rect width="510" height="240" rx="10" fill="#090d16" stroke="#161f30"/>
                    <circle cx="50" cy="50" r="24" fill="#162e12" stroke="#baff66"/>
                    <text x="50" y="56" fill="#baff66" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle">山</text>
                    <text x="90" y="45" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="bold">山田 太郎 (34歳 / 経験8年)</text>
                    <text x="90" y="65" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">シニアバックエンドエンジニア / GCP認定プロフェッショナル</text>
                    
                    <text x="30" y="110" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="13">マッチング根拠: Python/FastAPI 実務7年, GCP BigQuery/Cloud Run 設計実績</text>
                    <rect x="30" y="130" width="100" height="26" rx="6" fill="#162a15" stroke="#baff66"/>
                    <text x="45" y="148" fill="#baff66" font-family="Arial, sans-serif" font-size="11">一致: 98%</text>
                </g>

                <!-- Proposal Preview & Action -->
                <g transform="translate(20, 315)">
                    <rect width="510" height="400" rx="10" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">✉️ 自動生成 提案メール文面プレビュー</text>
                    <rect x="20" y="55" width="470" height="250" rx="6" fill="#04060a" stroke="#131b2e"/>
                    <text x="35" y="85" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">件名: 【ご提案】FinTech案件向け即戦力エンジニア（山田）のご推薦</text>
                    <text x="35" y="115" fill="#8b949e" font-family="Arial, sans-serif" font-size="11">サイバーソリューションズ ご担当者様</text>
                    <text x="35" y="135" fill="#8b949e" font-family="Arial, sans-serif" font-size="11">平素より大変お世話になっております。Mighty-Linkの佐藤です。</text>
                    <text x="35" y="155" fill="#8b949e" font-family="Arial, sans-serif" font-size="11">ご提示いただいたPython/GCPリード案件に合致する要員をご提案いたします...</text>
                    
                    <rect x="20" y="325" width="470" height="50" rx="8" fill="#162a15" stroke="#baff66"/>
                    <text x="255" y="357" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle">🚀 1-Click で提案メールを送信</text>
                </g>
            </g>
        </g>"""

    elif screen_key == "02_admin":
        return """
        <!-- Admin Dashboard & Audit Trail -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">管理者統合ダッシュボード ＆ 監査ログ</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">組織全体の権限ロール、APIクォータ消費、セキュリティログを一元監視</text>
            
            <!-- Top 3 Metrics Cards -->
            <g transform="translate(0, 80)">
                <rect width="340" height="110" rx="12" fill="#101726" stroke="#1e293b"/>
                <text x="20" y="35" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">アクティブユーザー数</text>
                <text x="20" y="75" fill="#ffffff" font-family="Arial, sans-serif" font-size="28" font-weight="bold">148 名</text>
                <text x="240" y="75" fill="#baff66" font-family="Arial, sans-serif" font-size="14">+12% (前月比)</text>
            </g>
            <g transform="translate(365, 80)">
                <rect width="340" height="110" rx="12" fill="#101726" stroke="#1e293b"/>
                <text x="20" y="35" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">月間APIクォータ消費率</text>
                <text x="20" y="75" fill="#8bdcff" font-family="Arial, sans-serif" font-size="28" font-weight="bold">42.8 %</text>
                <text x="240" y="75" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14">正常 (枠内)</text>
            </g>
            <g transform="translate(730, 80)">
                <rect width="340" height="110" rx="12" fill="#101726" stroke="#1e293b"/>
                <text x="20" y="35" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">セキュリティ脅威・ブロック</text>
                <text x="20" y="75" fill="#ffd166" font-family="Arial, sans-serif" font-size="28" font-weight="bold">0 件</text>
                <text x="240" y="75" fill="#baff66" font-family="Arial, sans-serif" font-size="14">完全健全</text>
            </g>

            <!-- Bottom: User Management Table & Audit Log Timeline -->
            <g transform="translate(0, 210)">
                <!-- User Table (650px) -->
                <rect width="650" height="610" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">👥 アカウント・権限ロール管理</text>
                
                <!-- Table Header -->
                <rect x="24" y="55" width="602" height="36" rx="6" fill="#090d16"/>
                <text x="40" y="78" fill="#8b949e" font-family="Arial, sans-serif" font-size="12" font-weight="bold">氏名 / メール</text>
                <text x="280" y="78" fill="#8b949e" font-family="Arial, sans-serif" font-size="12" font-weight="bold">ロール</text>
                <text x="420" y="78" fill="#8b949e" font-family="Arial, sans-serif" font-size="12" font-weight="bold">最終ログイン</text>
                <text x="550" y="78" fill="#8b949e" font-family="Arial, sans-serif" font-size="12" font-weight="bold">操作</text>

                <!-- Row 1 -->
                <g transform="translate(24, 100)">
                    <text x="16" y="24" fill="#ffffff" font-family="Arial, sans-serif" font-size="13">佐藤 賢太 (sato@...)</text>
                    <text x="256" y="24" fill="#baff66" font-family="Arial, sans-serif" font-size="12">最高統括管理者</text>
                    <text x="396" y="24" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">本日 09:12</text>
                    <rect x="520" y="6" width="60" height="24" rx="4" fill="#161f30"/>
                    <text x="535" y="22" fill="#8bdcff" font-family="Arial, sans-serif" font-size="11">編集</text>
                </g>
            </g>

            <!-- Right: Audit Logs (400px) -->
            <g transform="translate(670, 210)">
                <rect width="400" height="610" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">🛡️ セキュリティ監査ログ (リアルタイム)</text>
                <rect x="24" y="55" width="352" height="520" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="85" fill="#baff66" font-family="Arial, sans-serif" font-size="11">[09:12] User LOGIN: sato@... (2FA PASS)</text>
                <text x="40" y="115" fill="#8bdcff" font-family="Arial, sans-serif" font-size="11">[08:45] API SYNC: IMAP sales emails (12 ingested)</text>
                <text x="40" y="145" fill="#ffd166" font-family="Arial, sans-serif" font-size="11">[07:30] BACKUP: Supabase pg_dump OK (14.2MB)</text>
            </g>
        </g>"""

    elif screen_key == "03_attendance":
        return """
        <!-- Attendance & 36 Compliance -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">勤怠管理 ＆ 36協定・残業リスクAI解析</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">打刻集計・残業予測アラート・CSV一括インポートを完備</text>
            
            <!-- Left: Calendar / Timesheet (620px) -->
            <g transform="translate(0, 80)">
                <rect width="620" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">📅 2026年8月 勤務表カレンダー</text>
                
                <!-- Weekday Header -->
                <g transform="translate(24, 60)">
                    <rect width="572" height="30" rx="6" fill="#090d16"/>
                    <text x="30" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">月</text>
                    <text x="110" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">火</text>
                    <text x="190" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">水</text>
                    <text x="270" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">木</text>
                    <text x="350" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">金</text>
                    <text x="430" y="20" fill="#8bdcff" font-family="Arial, sans-serif" font-size="12">土</text>
                    <text x="510" y="20" fill="#ff7b72" font-family="Arial, sans-serif" font-size="12">日</text>
                </g>

                <!-- Sample Days Grid -->
                <rect x="24" y="100" width="572" height="520" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="50" y="140" fill="#baff66" font-family="Arial, sans-serif" font-size="12">09:00 - 18:00 (実働8h)</text>
                <text x="50" y="170" fill="#baff66" font-family="Arial, sans-serif" font-size="12">09:00 - 18:30 (残業0.5h)</text>

                <!-- Action Button -->
                <rect x="24" y="650" width="572" height="50" rx="10" fill="#162a15" stroke="#baff66"/>
                <text x="310" y="682" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle">⏱️ 現在時刻で出勤打刻</text>
            </g>

            <!-- Right: 36 Compliance Meter (430px) -->
            <g transform="translate(640, 80)">
                <rect width="430" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#ffd166" font-family="Arial, sans-serif" font-size="15" font-weight="bold">⚠️ 36協定・残業時間モニタリング</text>
                
                <!-- Gauge -->
                <g transform="translate(24, 70)">
                    <rect width="382" height="180" rx="10" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="35" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">当月累計残業時間</text>
                    <text x="20" y="80" fill="#baff66" font-family="Arial, sans-serif" font-size="36" font-weight="bold">14.5 <tspan font-size="18">/ 45.0 時間</tspan></text>
                    <rect x="20" y="110" width="342" height="14" rx="7" fill="#161f30"/>
                    <rect x="20" y="110" width="110" height="14" rx="7" fill="#baff66"/>
                    <text x="20" y="150" fill="#baff66" font-family="Arial, sans-serif" font-size="12">健全: 上限45時間まで残り 30.5時間</text>
                </g>

                <!-- CSV Ingest Box -->
                <g transform="translate(24, 280)">
                    <rect width="382" height="420" rx="10" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">📂 勤怠CSVインポート・一括解析</text>
                    <rect x="20" y="60" width="342" height="240" rx="8" fill="#04060a" stroke="#162a15" stroke-dasharray="6"/>
                    <text x="191" y="170" fill="#8b949e" font-family="Arial, sans-serif" font-size="13" text-anchor="middle">CSVファイルをここにドラッグ＆ドロップ</text>
                    <rect x="20" y="330" width="342" height="50" rx="8" fill="#131b2e" stroke="#1e293b"/>
                    <text x="191" y="362" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle">CSVファイルを選択</text>
                </g>
            </g>
        </g>"""

    elif screen_key == "04_survey":
        return """
        <!-- Survey / Employee Assessment -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">従業員向け適性・状況診断アンケート</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">現在の業務負荷・成長意欲・キャリア希望を迅速に可視化</text>
            
            <g transform="translate(0, 80)">
                <rect width="1070" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                
                <!-- Q1 -->
                <g transform="translate(30, 40)">
                    <text x="0" y="20" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">Q1. 現在のプロジェクトにおける業務負荷・スケジュール感はどうですか？</text>
                    <g transform="translate(0, 35)">
                        <circle cx="20" cy="15" r="8" fill="#162a15" stroke="#baff66"/>
                        <text x="36" y="20" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="13">1. 余裕がある</text>
                        <circle cx="160" cy="15" r="8" fill="#162a15" stroke="#baff66"/>
                        <circle cx="160" cy="15" r="4" fill="#baff66"/>
                        <text x="176" y="20" fill="#baff66" font-family="Arial, sans-serif" font-size="13" font-weight="bold">2. 適切・順調 (選択中)</text>
                        <circle cx="330" cy="15" r="8" fill="#090d16" stroke="#8b949e"/>
                        <text x="346" y="20" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">3. やや負荷が高い</text>
                    </g>
                </g>

                <!-- Q2 -->
                <g transform="translate(30, 140)">
                    <text x="0" y="20" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">Q2. 今後1年で特に習得・強化したい技術スタック・役割は？</text>
                    <rect x="0" y="35" width="1010" height="100" rx="8" fill="#090d16" stroke="#161f30"/>
                    <text x="20" y="65" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="13">AIエージェント開発およびクラウドネイティブアーキテクチャ設計</text>
                </g>

                <!-- Q3 -->
                <g transform="translate(30, 280)">
                    <text x="0" y="20" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">Q3. 直近のキャリア面談希望の有無</text>
                    <g transform="translate(0, 35)">
                        <circle cx="20" cy="15" r="8" fill="#162a15" stroke="#baff66"/>
                        <circle cx="20" cy="15" r="4" fill="#baff66"/>
                        <text x="36" y="20" fill="#baff66" font-family="Arial, sans-serif" font-size="13" font-weight="bold">希望する (今月中に面談設定)</text>
                    </g>
                </g>

                <!-- Submit Button -->
                <rect x="30" y="640" width="1010" height="56" rx="10" fill="#162a15" stroke="#baff66"/>
                <text x="535" y="675" fill="#baff66" font-family="Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle">📨 アンケート回答を送信</text>
            </g>
        </g>"""

    elif screen_key == "05_aptitude":
        return """
        <!-- Aptitude Demo & Feedback -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">自己診断デモ ＆ 面談フィードバックガイド</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">強み・適性・志向性を可視化し、面談での相互理解を加速</text>
            
            <g transform="translate(0, 80)">
                <!-- Left: 4-Quadrant Matrix (520px) -->
                <rect width="520" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">4象限コンピテンシー・ポジショニング</text>
                
                <rect x="24" y="60" width="472" height="472" rx="10" fill="#090d16" stroke="#161f30"/>
                <line x1="260" y1="60" x2="260" y2="532" stroke="#1e293b" stroke-width="2"/>
                <line x1="24" y1="296" x2="496" y2="296" stroke="#1e293b" stroke-width="2"/>
                
                <text x="260" y="85" fill="#8b949e" font-family="Arial, sans-serif" font-size="11" text-anchor="middle">イノベーション推進 ↑</text>
                <text x="260" y="520" fill="#8b949e" font-family="Arial, sans-serif" font-size="11" text-anchor="middle">安定運用・確実性 ↓</text>
                
                <circle cx="360" cy="180" r="14" fill="#162a15" stroke="#baff66" stroke-width="2"/>
                <text x="360" y="185" fill="#baff66" font-family="Arial, sans-serif" font-size="11" font-weight="bold" text-anchor="middle">現在地</text>

                <!-- Feedback Notes -->
                <rect x="24" y="550" width="472" height="160" rx="8" fill="#090d16" stroke="#161f30"/>
                <text x="40" y="580" fill="#baff66" font-family="Arial, sans-serif" font-size="13" font-weight="bold">💡 面談アドバイス・育成ポイント</text>
                <text x="40" y="610" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">新規技術へのキャッチアップが極めて速く、リードエンジニア適性が高評価。</text>
            </g>

            <!-- Right: Radar Chart Details (530px) -->
            <g transform="translate(540, 80)">
                <rect width="530" height="740" rx="14" fill="#101726" stroke="#1e293b"/>
                <text x="24" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="15" font-weight="bold">自己診断スコアサマリー</text>
                <rect x="24" y="60" width="482" height="650" rx="10" fill="#090d16" stroke="#161f30"/>
                <text x="50" y="100" fill="#ffffff" font-family="Arial, sans-serif" font-size="14">技術リーダーシップ: 92 点</text>
                <text x="50" y="140" fill="#ffffff" font-family="Arial, sans-serif" font-size="14">問題解決・仮説検証力: 95 点</text>
                <text x="50" y="180" fill="#ffffff" font-family="Arial, sans-serif" font-size="14">チームコラボレーション: 88 点</text>
            </g>
        </g>"""

    elif screen_key == "06_onboarding":
        return """
        <!-- Onboarding & Setup -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">初期セットアップ ＆ アカウント有効化</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">3ステップで組織設定・規約同意・アカウント有効化を完了</text>
            
            <!-- 3-Step Wizard Cards -->
            <g transform="translate(0, 80)">
                <!-- Step 1 (Done) -->
                <g transform="translate(0, 0)">
                    <rect width="340" height="450" rx="12" fill="#101726" stroke="#baff66" stroke-width="1.5"/>
                    <text x="20" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Step 1: 組織プロファイル</text>
                    <rect x="20" y="55" width="300" height="36" rx="6" fill="#090d16"/>
                    <text x="32" y="78" fill="#ffffff" font-family="Arial, sans-serif" font-size="12">社名: 株式会社マイティリンク</text>
                    <text x="20" y="420" fill="#baff66" font-family="Arial, sans-serif" font-size="12">✓ 設定完了</text>
                </g>

                <!-- Step 2 (Active) -->
                <g transform="translate(365, 0)">
                    <rect width="340" height="450" rx="12" fill="#162a15" stroke="#baff66" stroke-width="2"/>
                    <text x="20" y="35" fill="#baff66" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Step 2: 規約同意・法定開示</text>
                    <rect x="20" y="55" width="300" height="300" rx="6" fill="#090d16" stroke="#1e293b"/>
                    <text x="32" y="85" fill="#8b949e" font-family="Arial, sans-serif" font-size="11">利用規約、プライバシーポリシー、特商法表記</text>
                    <text x="20" y="420" fill="#ffd166" font-family="Arial, sans-serif" font-size="12">● 現在進行中 (同意チェック必須)</text>
                </g>

                <!-- Step 3 (Pending) -->
                <g transform="translate(730, 0)">
                    <rect width="340" height="450" rx="12" fill="#101726" stroke="#1e293b"/>
                    <text x="20" y="35" fill="#8b949e" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Step 3: アカウント有効化</text>
                    <rect x="20" y="55" width="300" height="300" rx="6" fill="#090d16"/>
                    <text x="20" y="420" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">○ 待機中</text>
                </g>

                <!-- Big Activation Action -->
                <g transform="translate(0, 480)">
                    <rect width="1070" height="260" rx="14" fill="#101726" stroke="#1e293b"/>
                    <text x="30" y="45" fill="#ffffff" font-family="Arial, sans-serif" font-size="16" font-weight="bold">利用規約・プライバシーポリシーに同意して有効化</text>
                    <rect x="30" y="160" width="1010" height="60" rx="10" fill="#162a15" stroke="#baff66"/>
                    <text x="535" y="197" fill="#baff66" font-family="Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle">🚀 アカウントを有効化して利用開始</text>
                </g>
            </g>
        </g>"""

    elif screen_key == "07_training":
        return """
        <!-- Training Guide 3-Course Curriculum -->
        <g transform="translate(30, 20)">
            <text x="0" y="30" fill="#ffffff" font-family="Arial, sans-serif" font-size="22" font-weight="bold">社内役割別研修・オンボーディングガイド</text>
            <text x="0" y="55" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">役割別カリキュラムを選択し、機能解説・受講ポイント・操作手順を確認</text>
            
            <g transform="translate(0, 80)">
                <!-- 3 Tabs Header -->
                <g transform="translate(0, 0)">
                    <rect width="340" height="45" rx="8" fill="#162a15" stroke="#baff66"/>
                    <text x="170" y="28" fill="#baff66" font-family="Arial, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">① 全社員基礎研修 (選択中)</text>
                </g>
                <g transform="translate(365, 0)">
                    <rect width="340" height="45" rx="8" fill="#101726" stroke="#1e293b"/>
                    <text x="170" y="28" fill="#8b949e" font-family="Arial, sans-serif" font-size="13" text-anchor="middle">② 営業・HR専門研修</text>
                </g>
                <g transform="translate(730, 0)">
                    <rect width="340" height="45" rx="8" fill="#101726" stroke="#1e293b"/>
                    <text x="170" y="28" fill="#8b949e" font-family="Arial, sans-serif" font-size="13" text-anchor="middle">③ 管理者管理研修</text>
                </g>

                <!-- Course 1 Panel Container -->
                <g transform="translate(0, 65)">
                    <rect width="1070" height="675" rx="14" fill="#101726" stroke="#1e293b"/>
                    
                    <text x="30" y="45" fill="#baff66" font-family="Arial, sans-serif" font-size="18" font-weight="bold">コース①: 全社員基礎研修（オンボーディング・勤怠・アンケート）</text>
                    <text x="30" y="75" fill="#8b949e" font-family="Arial, sans-serif" font-size="13">初期セットアップ、適性アンケート回答、勤怠打刻の手順を完全習得します。</text>

                    <!-- Curriculum Grid -->
                    <g transform="translate(30, 110)">
                        <rect width="490" height="180" rx="10" fill="#090d16" stroke="#161f30"/>
                        <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Lesson 1: 初期アクティベーション</text>
                        <text x="24" y="65" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">アカウント発行後の初期セットアップと規約同意フロー</text>
                        <rect x="24" y="115" width="200" height="40" rx="6" fill="#131b2e" stroke="#1e293b"/>
                        <text x="124" y="140" fill="#8bdcff" font-family="Arial, sans-serif" font-size="12" text-anchor="middle">⚙️ セットアップへ移動</text>
                    </g>

                    <g transform="translate(550, 110)">
                        <rect width="490" height="180" rx="10" fill="#090d16" stroke="#161f30"/>
                        <text x="24" y="35" fill="#8bdcff" font-family="Arial, sans-serif" font-size="14" font-weight="bold">Lesson 2: 勤怠打刻 ＆ 36協定理解</text>
                        <text x="24" y="65" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="12">打刻操作と月次残業時間の自己管理ポイント</text>
                        <rect x="24" y="115" width="200" height="40" rx="6" fill="#131b2e" stroke="#1e293b"/>
                        <text x="124" y="140" fill="#8bdcff" font-family="Arial, sans-serif" font-size="12" text-anchor="middle">⏱️ 勤怠管理へ移動</text>
                    </g>

                    <!-- Documentation Link Card (Single Tab) -->
                    <g transform="translate(30, 320)">
                        <rect width="1010" height="280" rx="10" fill="#090d16" stroke="#161f30"/>
                        <text x="30" y="45" fill="#ffffff" font-family="Arial, sans-serif" font-size="15" font-weight="bold">📚 研修詳細資料・ハンドブック (同一タブで閲覧)</text>
                        
                        <rect x="30" y="70" width="950" height="60" rx="8" fill="#131b2e" stroke="#1e293b"/>
                        <text x="50" y="105" fill="#8bdcff" font-family="Arial, sans-serif" font-size="13" font-weight="bold">📖 全社員向け基礎研修ハンドブック (FOUNDATION_TRAINING_HANDBOOK.md)</text>
                        
                        <rect x="30" y="145" width="950" height="60" rx="8" fill="#131b2e" stroke="#1e293b"/>
                        <text x="50" y="180" fill="#8bdcff" font-family="Arial, sans-serif" font-size="13" font-weight="bold">📖 開発ナレッジフロー・シーケンス図 (SEQUENCE_DIAGRAMS.md)</text>
                    </g>
                </g>
            </g>
        </g>"""

    return ""


def generate_all_wireframes():
    """Build SVG files for all application views and master artboard."""
    views = [
        ("00_home_fit_simulator.svg", "ホーム", "00: ホーム / AIフィットシミュレーター & ブランド動画", "00_home"),
        ("01_sales_matching_hub.svg", "営業メールマッチング", "01: 営業メールAIマッチング & 提案ハブ", "01_matching"),
        ("02_admin_dashboard.svg", "管理者ダッシュボード", "02: 管理者統合ダッシュボード & 監査ログ", "02_admin"),
        ("03_attendance_management.svg", "勤怠管理", "03: 勤怠管理 & 36協定AI解析", "03_attendance"),
        ("04_survey_assessment.svg", "適性アンケート", "04: 従業員適性・状況診断アンケート", "04_survey"),
        ("05_aptitude_demo.svg", "自己診断デモ", "05: 自己診断デモ & 面談活用ガイド", "05_aptitude"),
        ("06_onboarding_setup.svg", "初期セットアップ", "06: 初期セットアップ & アカウント有効化", "06_onboarding"),
        ("07_training_guide_curriculum.svg", "研修ガイド", "07: 社内役割別研修ガイド (3コース統合タブ)", "07_training"),
    ]

    master_svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 6200 2200" width="6200" height="2200" style="background:#030303;">
    <defs>
        <linearGradient id="bg-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#0b0f19"/>
            <stop offset="100%" stop-color="#030303"/>
        </linearGradient>
    </defs>
    <text x="40" y="60" fill="#ffffff" font-family="Arial, sans-serif" font-size="28" font-weight="900">MIGHTY SKILL-BRIDGE — 8 DISTINCT SCREENS MASTER WIREFRAME (2026 SaaS Parity)</text>
    <text x="40" y="90" fill="#8b949e" font-family="Arial, sans-serif" font-size="14">Unified Global Sidebar + Production-Accurate Viewport Designs</text>
    """

    for idx, (filename, tab_name, screen_title, screen_key) in enumerate(views):
        col = idx % 4
        row = idx // 4
        x_pos = 40 + col * 1520
        y_pos = 120 + row * 1020

        sidebar = build_sidebar_svg(tab_name)
        content_svg = get_screen_content(screen_key)
        
        screen_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 960" width="1440" height="960" style="background:url(#bg-grad);">
        {sidebar}
        <g id="Main_Content_Viewport" transform="translate(270, 20)">
            <rect width="1150" height="920" rx="20" fill="#0c101a" stroke="#161f30" stroke-width="1.2"/>
            {content_svg}
        </g>
        </svg>"""

        (OUTPUT_DIR / filename).write_text(screen_svg, encoding="utf-8")

        master_svg_content += f"""
        <g id="Frame_{idx}_{tab_name}" transform="translate({x_pos}, {y_pos})">
            {screen_svg}
        </g>"""

    master_svg_content += "\n</svg>"
    (OUTPUT_DIR / "mighty_link_full_wireframe_artboard.svg").write_text(master_svg_content, encoding="utf-8")
    print(f"[SUCCESS] Generated 8 distinct wireframes + master artboard in {OUTPUT_DIR}!")


if __name__ == "__main__":
    generate_all_wireframes()
