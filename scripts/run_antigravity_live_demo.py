#!/usr/bin/env python3
"""Fail closed unless the iterative Antigravity workshop demo is ready."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = PROJECT_ROOT / "docs" / "demo" / "antigravity_workshop"
SYNTHETIC_MARKER = "SYNTHETIC_DATA_ONLY"
PAGES_REPOSITORY = "https://github.com/kanta13jp1/mighty-link-antigravity-live-demo"
PAGES_URL = "https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class _SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.headings = {"h1": 0, "h2": 0, "h3": 0}
        self.buttons: list[dict[str, str]] = []
        self.external_refs: list[str] = []
        self.local_refs: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        self.tags.append(tag)
        if tag in self.headings:
            self.headings[tag] += 1
        if tag == "button":
            self.buttons.append(values)
        for name in ("href", "src"):
            value = values.get(name, "")
            if not value or value.startswith("#"):
                continue
            if value.startswith(("http://", "https://", "//")):
                self.external_refs.append(value)
            else:
                self.local_refs.append(value)

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.text_parts.append(text)


def _hypothesis_checks(files: dict[str, Path]) -> list[dict[str, object]]:
    prompt1 = _read_text(files["prompt1"])
    prompt2 = _read_text(files["prompt2"])
    prompt3 = _read_text(files["prompt3"])
    backup = _read_text(files["backup"])
    brief = _read_text(files["site_brief"])
    html = _read_text(files["output_html"])
    css = _read_text(files["output_css"])
    javascript = _read_text(files["output_js"])

    parser = _SiteParser()
    parser.feed(html)
    visible_text = " ".join(parser.text_parts)

    h1 = (
        prompt1.startswith("Prompt 1 / Webサイトを作る")
        and prompt2.startswith("Prompt 2 / 機能とデザインを改善する")
        and prompt3.startswith("Prompt 3 / GitHub Pagesへ公開する")
    )

    h2 = all(
        marker in prompt1
        for marker in (
            "index.html と styles.css",
            "この段階ではJavaScript",
            "git commitとgit pushは実行しない",
            "1440x900と390x844",
        )
    )

    h3 = all(
        marker in prompt2
        for marker in (
            "カテゴリ絞り込み",
            "参加候補に追加／追加済み",
            "app.jsを新規作成",
            "aria-pressed",
            "aria-live",
            "4、1、1、1、1",
            "git commitとgit pushは実行しない",
        )
    )

    prompt2_upper = prompt2.upper()
    css_upper = css.upper()
    h4 = (
        "#00A5E3" in prompt2_upper
        and "#EF7E00" in prompt2_upper
        and "#00A5E3" in css_upper
        and "#EF7E00" in css_upper
        and "gradient" not in css.lower()
    )

    h5 = (
        PAGES_REPOSITORY in prompt3
        and PAGES_URL in prompt3
        and "許可されたブランチ: main" in prompt3
        and "一致しない場合は何も変更せず停止" in prompt3
        and "mightylink-app.com" not in prompt3
        and "mighty-link-ai-connect" not in prompt3
    )

    h6 = all(
        marker in prompt3
        for marker in (
            "ここで必ず停止",
            "公開してもよいですか？",
            "正確に「公開して」と答えるまで",
            "git add、git commit、git push",
            "「公開して」と回答された後だけ",
        )
    )

    h7 = (
        SYNTHETIC_MARKER in brief
        and "実在する顧客、社員、申込情報を含まない" in brief
        and all(marker in prompt3 for marker in (".env", "トークン", "個人情報", "顧客情報"))
        and "フォーム送信、ネットワーク送信、永続保存は行わない" in brief
    )

    forbidden_runtime = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage")
    h8 = (
        not parser.external_refs
        and all((files["output_dir"] / ref).is_file() for ref in parser.local_refs if not ref.startswith("mailto:"))
        and not any(marker in javascript for marker in forbidden_runtime)
        and "form" not in parser.tags
        and files["hero_image"].stat().st_size > 100_000
    )

    filter_buttons = [button for button in parser.buttons if "data-filter" in button]
    select_buttons = [button for button in parser.buttons if "select-button" in button.get("class", "")]
    compact_css = re.sub(r"\s+", " ", css)
    h9 = (
        {"header", "main", "section", "footer"}.issubset(parser.tags)
        and parser.headings == {"h1": 1, "h2": 3, "h3": 4}
        and len(filter_buttons) == 5
        and len(select_buttons) == 4
        and all("aria-pressed" in button for button in parser.buttons)
        and 'name="viewport"' in html
        and "@media (max-width: 640px)" in compact_css
        and "grid-template-columns: 1fr" in compact_css
    )

    h10 = (
        all(marker in prompt3 for marker in ("最大3分", "HTTPS", "ページタイトル", "カテゴリ絞り込み", "参加候補2件"))
        and "90秒以上進展が見えない" in _read_text(files["readme"])
        and backup.count("ファイル変更、commit、pushは行わ") == 2
        and "ローカル予備成果物" in _read_text(files["output_readme"])
    )

    hypotheses = [
        ("H1_iterative_story", h1, "three prompts are explicitly ordered build, improve, publish"),
        ("H2_build_boundary", h2, "Prompt 1 builds HTML/CSS only and forbids commit/push"),
        ("H3_feature_iteration", h3, "Prompt 2 adds filters, shortlist behavior, ARIA, and tests"),
        ("H4_design_iteration", h4, "Prompt 2 and fallback site use official accent colors without gradients"),
        ("H5_publish_isolation", h5, f"dedicated repository={PAGES_REPOSITORY}"),
        ("H6_human_publish_gate", h6, "push is blocked until the exact human approval phrase"),
        ("H7_public_data_safety", h7, "synthetic-only brief and secret/PII checks are explicit"),
        ("H8_offline_fallback", h8, f"external_refs={len(parser.external_refs)}; local_refs={parser.local_refs}"),
        ("H9_responsive_accessibility", h9, f"headings={parser.headings}; buttons={len(parser.buttons)}"),
        ("H10_publish_verification_recovery", h10, "live URL verification and read-only recovery are defined"),
    ]
    return [
        {"name": name, "path": files["readme"], "passed": passed, "detail": detail}
        for name, passed, detail in hypotheses
    ]


def collect_demo_kit_status(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    workshop = project_root / "docs" / "demo" / "antigravity_workshop"
    output = workshop / "output"
    files = {
        "prompt1": workshop / "MAIN_PROMPT.txt",
        "prompt2": workshop / "PROMPT_02_IMPROVE.txt",
        "prompt3": workshop / "PROMPT_03_PUBLISH.txt",
        "backup": workshop / "BACKUP_PROMPTS.txt",
        "readme": workshop / "README.md",
        "site_brief": workshop / "input" / "SITE_BRIEF.md",
        "output_dir": output,
        "output_readme": output / "README.md",
        "output_html": output / "index.html",
        "output_css": output / "styles.css",
        "output_js": output / "app.js",
        "hero_image": output / "assets" / "workshop-hero.png",
    }

    checks: list[dict[str, object]] = []
    for name, path in files.items():
        if name == "output_dir":
            continue
        exists = path.is_file() and path.stat().st_size > 0
        checks.append({"name": name, "path": path, "passed": exists, "detail": "present" if exists else "missing"})

    if not all(check["passed"] for check in checks):
        return {"passed": False, "checks": checks}

    checks.extend(_hypothesis_checks(files))
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def verify_demo_data(project_root: Path = PROJECT_ROOT) -> int:
    result = collect_demo_kit_status(project_root)
    print("Google Antigravity 8/26 段階開発ライブデモ検証")
    print("=" * 60)
    for check in result["checks"]:
        status = "OK" if check["passed"] else "FAIL"
        path = Path(check["path"])
        try:
            display_path = path.relative_to(project_root)
        except ValueError:
            display_path = path
        print(f"[{status}] {check['name']}: {display_path} ({check['detail']})")
    message = "\n[PASS] 作成、改善、人の承認、専用Pages公開、確認、復旧を安全に実演できます。"
    if not result["passed"]:
        message = "\n[FAIL] デモキットの不足を修正してください。"
    print(message)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(verify_demo_data())
