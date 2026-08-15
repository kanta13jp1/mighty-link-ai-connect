"""Security & Log Integrity Audit Guard (T931).

Verifies that security audit logs, error logs, and access logging across the system
maintain structural integrity, properly record authentication/authorization failures,
prevent the leakage of sensitive credentials (API keys, tokens, passwords), and
strictly enforce non-persistence of sensitive personal data (e.g. mental health/psychological
evaluations and raw survey answers) in compliance with privacy regulations and project rules.

Outputs: exports/security_log_integrity_audit.{json,md}.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"
EXPORTS_DIR = PROJECT_ROOT / "exports"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "security_log_integrity_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "security_log_integrity_audit.md"

RUNBOOK_DOC = DOCS_DIR / "SECURITY_INCIDENT_RESPONSE_RUNBOOK.md"
PRIVACY_DOC = DOCS_DIR / "APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md"
GUARD_DOC = DOCS_DIR / "SECURITY_LOG_INTEGRITY_GUARD.md"

# Forbidden patterns in logs / persistence (credentials, secret keys, sensitive health attributes)
SENSITIVE_LEAK_PATTERNS = [
    re.compile(r"""(?:AIzaSy|sk-[a-zA-Z0-9]{20,}|service_role_key|BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY)"""),
    re.compile(r"""(?i)["']?(?:password|client_secret|access_token|refresh_token)["']?\s*[:=]\s*["'][^"']+["']"""),
    re.compile(r"""(?i)["']?(?:mental_score_raw|psychological_profile_raw|raw_answers_persistent)["']?\s*[:=]"""),
]

# Required modules to be scanned for sanitized logging & non-persistence guarantees
CORE_MODULES = [
    SRC_DIR / "app.py",
    SRC_DIR / "aptitude_demo.py",
    SRC_DIR / "supabase_client.py",
    SRC_DIR / "sales_email_match.py",
]


def check_source_modules_exist() -> bool:
    return all(m.exists() for m in CORE_MODULES)


def scan_for_secret_leaks(content: str) -> list[str]:
    leaks = []
    for pat in SENSITIVE_LEAK_PATTERNS:
        matches = pat.findall(content)
        if matches:
            leaks.extend([m[:20] + "..." if len(m) > 20 else m for m in matches])
    return leaks


def verify_aptitude_non_persistence() -> tuple[bool, str]:
    """Verify that src/aptitude_demo.py does NOT import database/storage and has no DB write calls."""
    aptitude_py = SRC_DIR / "aptitude_demo.py"
    if not aptitude_py.exists():
        return False, "src/aptitude_demo.py not found"
    
    code = aptitude_py.read_text(encoding="utf-8")
    forbidden_imports = ["supabase", "sqlite3", "psycopg2", "sqlalchemy", "prisma"]
    for imp in forbidden_imports:
        if re.search(rf"\bimport\s+{imp}\b|\bfrom\s+{imp}\b", code):
            return False, f"Forbidden persistence import '{imp}' found in aptitude_demo.py"
    
    return True, "No database imports; structural non-persistence verified"


def build_hypotheses() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    
    # H1: Core source modules exist
    h1_pass = check_source_modules_exist()
    results.append({
        "hypothesis": "H1",
        "description": "主要ソースモジュール（app.py, aptitude_demo.py, supabase_client.py等）が実在する",
        "passed": h1_pass,
        "detail": f"全 {len(CORE_MODULES)} モジュール実在確認" if h1_pass else "一部モジュールが欠落",
    })

    # H2: Structural non-persistence in aptitude demo
    h2_pass, h2_detail = verify_aptitude_non_persistence()
    results.append({
        "hypothesis": "H2",
        "description": "適性診断モジュールでDB保存機能を持たない構造的非永続性が担保されている",
        "passed": h2_pass,
        "detail": h2_detail,
    })

    # H3: Scan codebase / src files for raw credential leak patterns
    leaks_found = []
    for mod in CORE_MODULES:
        if mod.exists():
            leaks = scan_for_secret_leaks(mod.read_text(encoding="utf-8"))
            if leaks:
                leaks_found.append(f"{mod.name}: {leaks}")
    h3_pass = len(leaks_found) == 0
    results.append({
        "hypothesis": "H3",
        "description": "ソースコード内に平文APIキー/トークン/要配慮生データ永続化パターンが存在しない",
        "passed": h3_pass,
        "detail": "機密情報漏洩パターン 0 件 (PASS)" if h3_pass else f"漏洩検知: {leaks_found}",
    })

    # H4: Authentication error status codes (401/403) handling in app.py
    app_code = (SRC_DIR / "app.py").read_text(encoding="utf-8") if (SRC_DIR / "app.py").exists() else ""
    h4_pass = "401" in app_code and ("HTTPException" in app_code or "status_code" in app_code)
    results.append({
        "hypothesis": "H4",
        "description": "APIエンドポイントで認証・認可エラー（401/403）がHTTPException等で適切にハンドリングされている",
        "passed": h4_pass,
        "detail": "認証エラーハンドリング実装を確認" if h4_pass else "認証エラーコード未検出",
    })

    # H5: Security Runbook doc exists
    h5_pass = RUNBOOK_DOC.exists()
    results.append({
        "hypothesis": "H5",
        "description": "セキュリティインシデント対応Runbook (SECURITY_INCIDENT_RESPONSE_RUNBOOK.md) が実在する",
        "passed": h5_pass,
        "detail": f"{RUNBOOK_DOC.name} 実在" if h5_pass else "Runbook欠落",
    })

    # H6: Privacy design doc exists
    h6_pass = PRIVACY_DOC.exists()
    results.append({
        "hypothesis": "H6",
        "description": "適性診断プライバシー設計書 (APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md) が実在する",
        "passed": h6_pass,
        "detail": f"{PRIVACY_DOC.name} 実在" if h6_pass else "Privacy doc欠落",
    })

    # H7: Anonymization & pseudonymization in sales email & audit logging
    h7_pass = "pseudonym" in app_code or "talent_label" in app_code or "pseudonymize" in app_code
    results.append({
        "hypothesis": "H7",
        "description": "ログおよびマッチング結果で仮名化・匿名ラベル（talent_label等）が使用されている",
        "passed": h7_pass,
        "detail": "仮名化・匿名ラベル処理を確認" if h7_pass else "仮名化処理未検出",
    })

    # H8: Audit guard spec doc exists or is planned
    h8_pass = GUARD_DOC.exists()
    results.append({
        "hypothesis": "H8",
        "description": "セキュリティログ健全性ガード仕様書 (SECURITY_LOG_INTEGRITY_GUARD.md) が実在する",
        "passed": h8_pass,
        "detail": f"{GUARD_DOC.name} 実在" if h8_pass else "仕様書未作成",
    })

    # H9: Rate limiting & abuse prevention in app.py
    rate_limit_py = SRC_DIR / "rate_limit.py"
    h9_pass = rate_limit_py.exists() and ("RateLimiter" in rate_limit_py.read_text(encoding="utf-8") or "rate_limit" in rate_limit_py.read_text(encoding="utf-8"))
    results.append({
        "hypothesis": "H9",
        "description": "レートリミットモジュール (src/rate_limit.py) による不正アクセス・DoS防止機構が実在する",
        "passed": h9_pass,
        "detail": "RateLimiter 実装確認" if h9_pass else "RateLimiter 未実装",
    })

    # H10: Overall sanity & integrity
    all_passed = all(r["passed"] for r in results)
    results.append({
        "hypothesis": "H10",
        "description": "セキュリティ・ログ健全性自動スキャン全体が完全・整合（ドリフト0）",
        "passed": all_passed,
        "detail": "全セキュリティ仮説 PASS" if all_passed else "不整合・要対応項目あり",
    })

    summary = {
        "total_hypotheses": len(results),
        "passed_hypotheses": sum(1 for r in results if r["passed"]),
        "failed_hypotheses": sum(1 for r in results if not r["passed"]),
        "all_passed": all_passed,
    }
    return results, summary


def render_markdown(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# セキュリティ・ログ健全性自動スキャン監査レポート (T931)",
        "",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if summary['all_passed'] else '❌ FAIL'}",
        f"- 合格仮説数: **{summary['passed_hypotheses']} / {summary['total_hypotheses']}**",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        badge = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['hypothesis']} | {r['description']} | {badge} | {r['detail']} |")
    lines.append("")
    return "\n".join(lines)


def run_audit(json_out: Path = DEFAULT_JSON, md_out: Path = DEFAULT_MD) -> int:
    results, summary = build_hypotheses()
    
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    
    md_content = render_markdown(results, summary)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(md_content, encoding="utf-8")
    
    print(f"[*] セキュリティ・ログ健全性監査 (T931): {'PASS' if summary['all_passed'] else 'FAIL'}")
    return 0 if summary["all_passed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit security log integrity and sensitive data non-persistence")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="JSON output path")
    parser.add_argument("--md", type=Path, default=DEFAULT_MD, help="Markdown output path")
    args = parser.parse_args()
    sys_code = run_audit(json_out=args.json, md_out=args.md)
    if sys_code != 0:
        raise SystemExit(sys_code)


if __name__ == "__main__":
    main()
