"""Add high-score alert banner and filterHighScoreMatches function to index.html and src/index.html."""

from pathlib import Path

def patch():
    html_path = Path("index.html")
    content = html_path.read_text(encoding="utf-8")
    
    target_toolbar = '<div class="matching-filter-toolbar" role="search" aria-label="営業メールAIマッチングの絞り込み">'
    alert_banner = '''<div id="high-score-alert-banner" style="margin-bottom: 16px; background: linear-gradient(90deg, rgba(186, 255, 102, 0.08), rgba(139, 220, 255, 0.08)); border: 1px solid rgba(186, 255, 102, 0.3); border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 18px;">🚀</span>
                            <div>
                                <div style="font-size: 13px; font-weight: bold; color: var(--text);">【速報】適合度90%以上の即時提案可能マッチングが検出されています</div>
                                <div style="font-size: 11px; color: var(--muted);">AIが抽出した高確度ペアを1クリックでクライアントへ提案可能です</div>
                            </div>
                        </div>
                        <button type="button" class="btn" style="padding: 6px 14px; font-size: 11px; font-weight: bold; background: rgba(186, 255, 102, 0.15); border: 1px solid rgba(186, 255, 102, 0.4); color: var(--green); border-radius: 6px; cursor: pointer;" onclick="filterHighScoreMatches()">🔥 適合度90%以上のみ表示</button>
                    </div>

                    ''' + target_toolbar

    if target_toolbar in content and "high-score-alert-banner" not in content:
        content = content.replace(target_toolbar, alert_banner)
        
    js_target = "function resetMatchingFilters() {"
    new_js = """function filterHighScoreMatches() {
            const scoreSelect = document.getElementById("matching-filter-score");
            if (scoreSelect) {
                scoreSelect.value = "90";
                applyMatchingFilters();
            }
        }

        function resetMatchingFilters() {"""
    
    if js_target in content and "function filterHighScoreMatches()" not in content:
        content = content.replace(js_target, new_js)
        
    html_path.write_text(content, encoding="utf-8")
    Path("src/index.html").write_text(content, encoding="utf-8")
    print("[+] Successfully added high-score alert banner to index.html and src/index.html")

if __name__ == "__main__":
    patch()
