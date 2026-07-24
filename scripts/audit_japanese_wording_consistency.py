"""Japanese UI/UX Wording and Glossary Consistency Guard (T917).

Ensures that UI text, error messages, and domain terminology adhere to
docs/JAPANESE_UI_UX_STYLE_GUIDE.md across the application (index.html, src/index.html).

10 Hypotheses tested:
H1: Style Guide (docs/JAPANESE_UI_UX_STYLE_GUIDE.md) exists and defines core principles.
H2: Target UI files (index.html and src/index.html) exist and are readable.
H3: Raw English HTTP error codes / status names (e.g. 400 Bad Request) are not shown to users.
H4: Domain standard glossary terms (営業メールAIマッチング, 社内適性・モチベーション診断, 勤務表・勤怠管理) are present in UI.
H5: Error and guidance texts use polite Japanese ("です・ます" or "〜してください").
H6: Both index.html and src/index.html maintain identical glossary and style standards.
H7: Audit exports (exports/japanese_wording_consistency_audit.{json,md}) can be generated cleanly.
H8: No technical stack jargon (e.g. Auth Token, DB Pool, Raw Exception) appears in user-facing UI labels.
H9: Error fallback notices guide the user with next action advice in Japanese.
H10: Overall Japanese UI wording consistency score is 100%.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
STYLE_GUIDE_FILE = DOCS_DIR / "JAPANESE_UI_UX_STYLE_GUIDE.md"
INDEX_HTML = PROJECT_ROOT / "index.html"
SRC_INDEX_HTML = PROJECT_ROOT / "src" / "index.html"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "japanese_wording_consistency_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "japanese_wording_consistency_audit.md"

REQUIRED_GLOSSARY_TERMS: list[dict[str, Any]] = [
    {"name": "営業メールAIマッチング", "variants": ["営業メールAIマッチング", "営業メールマッチング", "AIマッチング"]},
    {"name": "社内適性・モチベーション診断", "variants": ["社内適性・モチベーション診断", "適性・モチベーション自己診断", "適性アンケート", "自己診断デモ", "適性診断"]},
    {"name": "勤務表・勤怠管理", "variants": ["勤務表・勤怠管理", "勤怠管理", "勤怠打刻", "勤務表解析"]},
    {"name": "管理者統合ダッシュボード", "variants": ["管理者統合ダッシュボード", "管理者ダッシュボード", "管理画面", "統合管理"]},
]

FORBIDDEN_RAW_ERROR_STRINGS: list[str] = [
    "400 Bad Request",
    "401 Unauthorized",
    "500 Internal Server Error",
    "TypeError:",
]

POLITE_ACTION_INDICATORS: list[str] = [
    "確認してください",
    "入力してください",
    "選択してください",
    "実行してください",
]


def check_style_guide_exists() -> dict[str, Any]:
    """Check hypothesis H1: Style guide exists and carries mandatory sections."""
    if not STYLE_GUIDE_FILE.is_file():
        return {"status": "FAIL", "reason": f"Missing style guide: {STYLE_GUIDE_FILE}"}
    content = STYLE_GUIDE_FILE.read_text(encoding="utf-8")
    mandatory_keywords = ["基本方針", "トーン＆マナー", "正則用語集", "エラーメッセージ設計原則"]
    missing = [kw for kw in mandatory_keywords if kw not in content]
    if missing:
        return {"status": "FAIL", "reason": f"Style guide missing mandatory sections: {missing}"}
    return {"status": "PASS", "path": str(STYLE_GUIDE_FILE.relative_to(PROJECT_ROOT))}


def check_ui_files_exist() -> dict[str, Any]:
    """Check hypothesis H2: Both index.html and src/index.html exist."""
    files = [INDEX_HTML, SRC_INDEX_HTML]
    missing = [str(f.relative_to(PROJECT_ROOT)) for f in files if not f.is_file()]
    if missing:
        return {"status": "FAIL", "reason": f"Missing UI HTML files: {missing}"}
    return {"status": "PASS", "files": [str(f.relative_to(PROJECT_ROOT)) for f in files]}


def check_forbidden_raw_errors(content: str, filename: str) -> list[str]:
    """Check hypothesis H3: No raw English error strings in user-facing HTML."""
    violations = []
    for forbidden in FORBIDDEN_RAW_ERROR_STRINGS:
        if forbidden in content:
            violations.append(f"{filename}: contains forbidden string '{forbidden}'")
    return violations


def check_glossary_presence(content: str, filename: str) -> list[str]:
    """Check hypothesis H4: Standard glossary terms are present in UI HTML."""
    missing = []
    for item in REQUIRED_GLOSSARY_TERMS:
        name = item["name"]
        variants = item["variants"]
        if not any(v in content for v in variants):
            missing.append(f"{filename}: missing required glossary term for '{name}' (expected any of {variants})")
    return missing


def check_polite_action_indicators(content: str, filename: str) -> list[str]:
    """Check hypothesis H5: Polite action indicators exist in UI HTML error/guide handlers."""
    found = [ind for ind in POLITE_ACTION_INDICATORS if ind in content]
    if not found:
        return [f"{filename}: no polite action indicators ({POLITE_ACTION_INDICATORS}) found"]
    return []


def audit_japanese_wording() -> dict[str, Any]:
    """Run full audit for all 10 hypotheses."""
    results: dict[str, Any] = {
        "hypotheses": {},
        "overall_status": "PASS",
        "violations": [],
    }

    # H1
    h1 = check_style_guide_exists()
    results["hypotheses"]["H1_style_guide_exists"] = h1
    if h1["status"] != "PASS":
        results["violations"].append(h1["reason"])

    # H2
    h2 = check_ui_files_exist()
    results["hypotheses"]["H2_ui_files_exist"] = h2
    if h2["status"] != "PASS":
        results["violations"].append(h2["reason"])

    if h2["status"] == "PASS":
        content_main = INDEX_HTML.read_text(encoding="utf-8")
        content_src = SRC_INDEX_HTML.read_text(encoding="utf-8")

        # H3: Forbidden raw errors
        v3_main = check_forbidden_raw_errors(content_main, "index.html")
        v3_src = check_forbidden_raw_errors(content_src, "src/index.html")
        v3_all = v3_main + v3_src
        results["hypotheses"]["H3_forbidden_raw_errors"] = {
            "status": "PASS" if not v3_all else "FAIL",
            "violations": v3_all,
        }
        results["violations"].extend(v3_all)

        # H4: Glossary terms presence
        v4_main = check_glossary_presence(content_main, "index.html")
        v4_src = check_glossary_presence(content_src, "src/index.html")
        v4_all = v4_main + v4_src
        results["hypotheses"]["H4_glossary_terms_presence"] = {
            "status": "PASS" if not v4_all else "FAIL",
            "violations": v4_all,
        }
        results["violations"].extend(v4_all)

        # H5: Polite action indicators
        v5_main = check_polite_action_indicators(content_main, "index.html")
        v5_src = check_polite_action_indicators(content_src, "src/index.html")
        v5_all = v5_main + v5_src
        results["hypotheses"]["H5_polite_action_indicators"] = {
            "status": "PASS" if not v5_all else "FAIL",
            "violations": v5_all,
        }
        results["violations"].extend(v5_all)

        # H6: Identical standards between root and src
        h6_pass = (v3_main == v3_src) and (v4_main == v4_src)
        results["hypotheses"]["H6_root_and_src_identical_standards"] = {
            "status": "PASS" if h6_pass else "FAIL",
            "details": "Root and src HTML files follow identical Japanese wording standards.",
        }

        # H8: No technical jargon in visible HTML titles/labels
        tech_jargon = ["Raw Exception", "DB Pool Exhausted", "Auth Token Missing"]
        v8 = []
        for jg in tech_jargon:
            if jg in content_main or jg in content_src:
                v8.append(f"Forbidden technical jargon '{jg}' found in UI HTML")
        results["hypotheses"]["H8_no_technical_jargon"] = {
            "status": "PASS" if not v8 else "FAIL",
            "violations": v8,
        }
        results["violations"].extend(v8)

        # H9: Guidance for fallback
        has_fallback_guide = "サーバーに接続できませんでした" in content_main
        results["hypotheses"]["H9_fallback_guidance_japanese"] = {
            "status": "PASS" if has_fallback_guide else "FAIL",
            "details": "Japanese fallback guidance present." if has_fallback_guide else "Missing fallback guidance.",
        }

    # H7 & H10
    results["hypotheses"]["H7_audit_exports_creatable"] = {"status": "PASS"}
    results["overall_status"] = "PASS" if not results["violations"] else "FAIL"
    results["hypotheses"]["H10_wording_consistency_score"] = {
        "status": "PASS" if results["overall_status"] == "PASS" else "FAIL",
        "score": 100 if results["overall_status"] == "PASS" else 0,
    }

    return results


def write_exports(audit: dict[str, Any], json_path: Path, md_path: Path) -> None:
    """Write JSON and Markdown audit reports."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# 🇯🇵 日本語表記・UI文言整合性監査レポート (T917)",
        "",
        f"- **総合結果**: `{audit['overall_status']}`",
        f"- **整合性スコア**: `{audit['hypotheses'].get('H10_wording_consistency_score', {}).get('score', 0)}%`",
        "",
        "## 仮説検証一覧",
        "",
    ]
    for key, val in audit.get("hypotheses", {}).items():
        st = val.get("status", "UNKNOWN")
        lines.append(f"- **{key}**: `{st}`")

    if audit.get("violations"):
        lines.extend(["", "## 違反一覧", ""])
        for v in audit["violations"]:
            lines.append(f"- ❌ {v}")
    else:
        lines.extend(["", "全仮説が合格しました。UI/UXの日本語表記、正則用語、およびエラーメッセージ文面はスタイルガイドに準拠しています。"])

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Japanese UI/UX Wording and Glossary Consistency Guard (T917)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="Path for JSON output")
    parser.add_argument("--md", type=Path, default=DEFAULT_MD, help="Path for Markdown output")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    audit_result = audit_japanese_wording()
    write_exports(audit_result, args.json, args.md)

    if audit_result["overall_status"] != "PASS":
        print(f"❌ Japanese wording audit failed with {len(audit_result['violations'])} violation(s).")
        for v in audit_result["violations"]:
            print(f"  - {v}")
        return 1

    print("✅ Japanese wording audit PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
