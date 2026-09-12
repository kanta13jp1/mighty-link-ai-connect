"""Patch index.html and src/index.html to remove hardcoded numbers and render dynamic source breakdown."""

from pathlib import Path
import re

OLD_HERO_HTML = """                    <!-- 4連 ヒーローメトリクスカード -->
                    <div class="analytics-hero-grid">
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">📩 総取り込みメール件数</span>
                            <div class="analytics-hero-val" id="analytics-hero-total">694 <small>件</small></div>
                            <span class="analytics-hero-sub">✓ 安全同期完了 (IMAP 読取専用)</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">🎯 AI抽出案件数</span>
                            <div class="analytics-hero-val" id="analytics-hero-extracted">694 <small>件</small></div>
                            <span class="analytics-hero-sub" style="color:var(--blue)">構造化率 100%</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">💰 平均推定単価</span>
                            <div class="analytics-hero-val" id="analytics-hero-rate">78.5 <small>万円/月</small></div>
                            <span class="analytics-hero-sub" style="color:var(--yellow)">最高 140万円</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">🏢 主要パートナー企業数</span>
                            <div class="analytics-hero-val" id="analytics-hero-domains">12 <small>社</small></div>
                            <span class="analytics-hero-sub" style="color:var(--green)">お名前.com / GMO等</span>
                        </div>
                    </div>"""

NEW_HERO_HTML = """                    <!-- 4連 ヒーローメトリクスカード (動的レンダリング) -->
                    <div class="analytics-hero-grid">
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">📊 総解析データ</span>
                            <div class="analytics-hero-val" id="analytics-hero-total"><span style="font-size:16px;color:var(--muted)">取得中...</span></div>
                            <span class="analytics-hero-sub">全件構造化・重複照合済</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">📩 メールサーバー直接取得履歴</span>
                            <div class="analytics-hero-val" id="analytics-hero-server"><span style="font-size:16px;color:var(--muted)">取得中...</span></div>
                            <span class="analytics-hero-sub" style="color:var(--blue)">IMAP / POP3 直接取得</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">📂 Thunderbird復旧データ</span>
                            <div class="analytics-hero-val" id="analytics-hero-restored"><span style="font-size:16px;color:var(--muted)">取得中...</span></div>
                            <span class="analytics-hero-sub" style="color:var(--yellow)">ローカルアーカイブ復元</span>
                        </div>
                        <div class="analytics-hero-card">
                            <span class="analytics-hero-label">⚡ 本日の新着</span>
                            <div class="analytics-hero-val" id="analytics-hero-today"><span style="font-size:16px;color:var(--muted)">取得中...</span></div>
                            <span class="analytics-hero-sub" style="color:var(--green)">当日IMAP取得分</span>
                        </div>
                    </div>"""

OLD_JS_REGEX = re.compile(
    r"const FALLBACK_SALES_EMAIL_ANALYTICS = \{.*?\};\s*function renderAnalyticsPanels\(data\)\s*\{.*?\}\s*async function loadSalesEmailAnalytics\(\)\s*\{.*?\}",
    re.DOTALL
)

NEW_JS = """function renderAnalyticsPanels(data) {
            if (!data) return;
            const totalEl = document.getElementById("analytics-hero-total");
            if (totalEl) totalEl.innerHTML = (typeof data.total_count === "number") ? `${data.total_count.toLocaleString()} <small>件</small>` : "取得中...";
            
            const serverEl = document.getElementById("analytics-hero-server");
            if (serverEl) serverEl.innerHTML = (typeof data.server_direct_count === "number") ? `${data.server_direct_count.toLocaleString()} <small>件</small>` : "取得中...";
            
            const restoredEl = document.getElementById("analytics-hero-restored");
            if (restoredEl) restoredEl.innerHTML = (typeof data.local_restored_count === "number") ? `${data.local_restored_count.toLocaleString()} <small>件</small>` : "取得中...";
            
            const todayEl = document.getElementById("analytics-hero-today");
            if (todayEl) todayEl.innerHTML = (typeof data.today_new_count === "number") ? `${data.today_new_count.toLocaleString()} <small>件</small>` : "0 <small>件</small>";

            const dailyDiv = document.getElementById("analytics-daily-list");
            if (dailyDiv) {
                const entries = Object.entries(data.daily_counts || {}).sort((a, b) => b[0].localeCompare(a[0]));
                if (entries.length === 0) {
                    dailyDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">データがありません</span>`;
                } else {
                    const maxCount = Math.max(...entries.map(e => e[1]), 1);
                    dailyDiv.innerHTML = entries.map(([date, count]) => `
                        <div style="display: flex; align-items: center; justify-content: space-between; font-size: 13px;">
                            <span style="font-weight: 500; font-family: monospace;">${escapeHtml(date)}</span>
                            <div style="display: flex; align-items: center; gap: 8px; flex: 1; margin-left: 16px; justify-content: flex-end;">
                                <div style="height: 6px; background: linear-gradient(90deg, #8bdcff, #4fd1a5); border-radius: 3px; width: ${Math.min(100, (count / maxCount) * 100)}%; max-width: 120px; box-shadow: 0 0 8px rgba(139,220,255,0.4);"></div>
                                <span style="font-weight: 600; color: var(--text); min-width: 36px; text-align: right;">${count} 件</span>
                            </div>
                        </div>
                    `).join("");
                }
            }
            
            const domainDiv = document.getElementById("analytics-domain-list");
            if (domainDiv) {
                const entries = Object.entries(data.domain_counts || {}).sort((a, b) => b[1] - a[1]);
                const totalDomainEntries = entries.reduce((sum, e) => sum + e[1], 0) || 1;
                if (entries.length === 0) {
                    domainDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">データがありません</span>`;
                } else {
                    domainDiv.innerHTML = entries.map(([domain, count]) => {
                        const pct = Math.round((count / totalDomainEntries) * 100);
                        return `
                            <div style="display: flex; flex-direction: column; gap: 4px; font-size: 13px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 500; font-family: monospace; color: var(--text);">${escapeHtml(domain)}</span>
                                    <span style="font-weight: bold; color: var(--blue);">${count} 通 <small style="color:var(--muted);font-weight:normal">(${pct}%)</small></span>
                                </div>
                                <div style="height: 4px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
                                    <div style="height: 100%; width: ${pct}%; background: linear-gradient(90deg, #8bdcff, #4fd1a5); border-radius: 999px;"></div>
                                </div>
                            </div>
                        `;
                    }).join("");
                }
            }
            
            const skillDiv = document.getElementById("analytics-skill-list");
            if (skillDiv) {
                const entries = Object.entries(data.skill_counts || {}).sort((a, b) => b[1] - a[1]);
                const maxSkillCount = Math.max(...entries.map(e => e[1]), 1);
                if (entries.length === 0) {
                    skillDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">データがありません</span>`;
                } else {
                    skillDiv.innerHTML = entries.map(([skill, count]) => {
                        const pct = Math.round((count / maxSkillCount) * 100);
                        return `
                            <div style="display: flex; flex-direction: column; gap: 4px; font-size: 13px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span class="fit-badge fit-med" style="font-size: 11px; padding: 2px 8px; border-radius: 4px;">${escapeHtml(skill)}</span>
                                    <span style="font-weight: bold; color: var(--green);">${count} 回</span>
                                </div>
                                <div style="height: 4px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
                                    <div style="height: 100%; width: ${pct}%; background: linear-gradient(90deg, #4fd1a5, #e6c15a); border-radius: 999px;"></div>
                                </div>
                            </div>
                        `;
                    }).join("");
                }
            }
        }

        function renderAnalyticsError() {
            const totalEl = document.getElementById("analytics-hero-total");
            if (totalEl) totalEl.innerHTML = `<span style="font-size:14px;color:var(--muted)">取得失敗</span>`;
            const serverEl = document.getElementById("analytics-hero-server");
            if (serverEl) serverEl.innerHTML = `<span style="font-size:14px;color:var(--muted)">取得失敗</span>`;
            const restoredEl = document.getElementById("analytics-hero-restored");
            if (restoredEl) restoredEl.innerHTML = `<span style="font-size:14px;color:var(--muted)">取得失敗</span>`;
            const todayEl = document.getElementById("analytics-hero-today");
            if (todayEl) todayEl.innerHTML = `<span style="font-size:14px;color:var(--muted)">取得失敗</span>`;

            const dailyDiv = document.getElementById("analytics-daily-list");
            if (dailyDiv) dailyDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">統計データの取得に失敗しました</span>`;
            const domainDiv = document.getElementById("analytics-domain-list");
            if (domainDiv) domainDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">統計データの取得に失敗しました</span>`;
            const skillDiv = document.getElementById("analytics-skill-list");
            if (skillDiv) skillDiv.innerHTML = `<span style="color:var(--muted);font-size:12px;">統計データの取得に失敗しました</span>`;
        }

        async function loadSalesEmailAnalytics() {
            try {
                const res = await fetch("/api/sales-email/analytics");
                if (!res.ok) {
                    renderAnalyticsError();
                    return;
                }
                const data = await res.json();
                if (data && data.status === "success") {
                    renderAnalyticsPanels(data);
                } else {
                    renderAnalyticsError();
                }
            } catch (e) {
                renderAnalyticsError();
            }
        }"""


def patch():
    for path_str in ["index.html", "src/index.html"]:
        p = Path(path_str)
        if not p.exists():
            continue
        c = p.read_text(encoding="utf-8")
        
        # 1. Update Title and subtitle
        c = c.replace("営業メール解析統計・トレンド (694件全件解析)", "営業メール解析統計・トレンド")
        c = c.replace("営業メール解析統計・トレンド (691件全件解析)", "営業メール解析統計・トレンド")
        c = c.replace("お名前.com/GMOサーバーから取り込んだ694件の営業メールのリアルタイムAI統計分析", "メールサーバー直接取得および復旧データのリアルタイムAI統計分析")
        c = c.replace("お名前.com/GMOサーバーから取り込んだ691件の営業メールのリアルタイムAI統計分析", "メールサーバー直接取得および復旧データのリアルタイムAI統計分析")
        
        # 2. Update Hero Cards
        c = c.replace(OLD_HERO_HTML, NEW_HERO_HTML)
        
        # 3. Update JavaScript
        c = OLD_JS_REGEX.sub(NEW_JS, c)
        
        p.write_text(c, encoding="utf-8")
        print(f"[+] Patched {path_str} successfully.")

if __name__ == "__main__":
    patch()
