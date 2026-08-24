"""Patch index.html and src/index.html to include mailto launcher button and safe IMAP label."""

from pathlib import Path

def patch():
    html_path = Path("index.html")
    content = html_path.read_text(encoding="utf-8")
    
    # 1. Update IMAP label
    content = content.replace("✓ 全件解析完了 (IMAP/POP3)", "✓ 安全同期完了 (IMAP 読取専用)")
    
    # 2. Add mailto launcher button
    target_btn = '<button type="button" class="btn" style="padding: 8px 20px; font-size: 12px; font-weight: bold; background: linear-gradient(90deg, var(--green), var(--blue)); border: none; border-radius: 6px; color: #030303; cursor: pointer; box-shadow: 0 0 15px rgba(186, 255, 102, 0.2);" onclick="copyProposalToClipboard()">📋 提案文をコピー</button>'
    new_btns = '<button type="button" class="btn" style="padding: 8px 16px; font-size: 12px; font-weight: bold; background: rgba(139, 220, 255, 0.12); border: 1px solid rgba(139, 220, 255, 0.3); border-radius: 6px; color: var(--blue); cursor: pointer;" onclick="launchMailerWithProposal()">📨 メーラーを起動</button>\n                    ' + target_btn
    
    if target_btn in content and "launchMailerWithProposal()" not in content:
        content = content.replace(target_btn, new_btns)
        
    # 3. Add JS function
    func_target = 'function copyProposalToClipboard() {'
    new_func = """function launchMailerWithProposal() {
            const subject = encodeURIComponent(document.getElementById("proposal-subject-input").value || "");
            const body = encodeURIComponent(document.getElementById("proposal-body-textarea").value || "");
            window.location.href = `mailto:?subject=${subject}&body=${body}`;
        }

        function copyProposalToClipboard() {"""
    
    if func_target in content and "function launchMailerWithProposal()" not in content:
        content = content.replace(func_target, new_func)
        
    html_path.write_text(content, encoding="utf-8")
    Path("src/index.html").write_text(content, encoding="utf-8")
    print("[+] Successfully patched index.html and src/index.html")

if __name__ == "__main__":
    patch()
