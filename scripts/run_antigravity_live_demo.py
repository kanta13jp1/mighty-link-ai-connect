#!/usr/bin/env python3
"""Fail closed unless the skills-led Antigravity workshop demo is ready."""

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


def _hypothesis_checks(files: dict[str, Path]) -> list[dict[str, object]]:
    prompts = [_read_text(files[f"prompt{number}"]) for number in range(6)]
    grill, find_skills, build, steer, mcp, publish = prompts
    concepts = _read_text(files["concepts"])
    backup = _read_text(files["backup"])
    readme = _read_text(files["readme"])
    brief = _read_text(files["site_brief"])
    html = _read_text(files["output_html"])
    css = _read_text(files["output_css"])
    javascript = _read_text(files["output_js"])

    parser = _SiteParser()
    parser.feed(html)

    h1 = (
        all(prompt.startswith(f"Prompt {number} /") for number, prompt in enumerate(prompts))
        and all(
            name in readme
            for name in (
                "PROMPT_00_GRILL_ME.txt",
                "PROMPT_01_FIND_SKILLS.txt",
                "PROMPT_02_BUILD.txt",
                "PROMPT_03_STEER.txt",
                "PROMPT_04_MCP_CHECK.txt",
                "PROMPT_05_PUBLISH.txt",
            )
        )
        and "20分" in readme
    )

    h2 = all(
        marker in grill
        for marker in (
            "/grill-me",
            "次の6点を1問ずつ質問",
            "私の回答を待って",
            "決定事項／見送ること／停止条件／成功条件",
            "ファイル変更、コマンド実行、外部通信を行わない",
        )
    )

    h3 = all(
        marker in find_skills
        for marker in (
            "/find-skills",
            "frontend design",
            "web accessibility",
            "GitHub Pages deployment",
            "インストール数",
            "公開元とGitHub stars",
            "セキュリティ監査",
            "まだSkillのインストール",
        )
    )

    h4 = all(
        marker in build
        for marker in (
            "@SITE_BRIEF.md",
            "index.html と styles.css",
            "この段階ではJavaScript",
            "commitとpushは実行しない",
            "1440x900と390x844",
        )
    )

    h5 = all(
        marker in steer
        for marker in (
            "Steering",
            "変更すること",
            "維持すること",
            "検証すること",
            "aria-pressed",
            "aria-live",
            "#00A5E3",
            "#EF7E00",
            "4、1、1、1、1",
            "2件選択",
        )
    )

    h6 = all(
        marker in concepts
        for marker in (
            "## Skills",
            "SKILL.md",
            "再利用可能なパッケージ",
            "/grill-me",
            "/find-skills",
            "anthropics/skills@frontend-design",
            "Agent Skills",
        )
    )

    h7 = all(
        marker in mcp
        for marker in (
            "/mcp",
            "GitHub MCP",
            "読み取り専用",
            "Issue作成、設定変更、認証の追加、ファイル変更、commit、pushは行わない",
            "MCP確認は省略、gitと公開URL確認へ継続",
        )
    ) and all(marker in concepts for marker in ("## MCP", "Model Context Protocol", "標準形式"))

    h8 = all(
        marker in concepts
        for marker in (
            "## Steering",
            "## Power",
            "公式機能名ではなく",
            "研修上の呼称",
            "独立設定があるとは説明しない",
        )
    ) and "`Power`はAntigravityの公式機能名として扱いません" in readme

    h9 = (
        PAGES_REPOSITORY in publish
        and PAGES_URL in publish
        and "remoteまたはbranchが一致しなければ何も変更せず停止" in publish
        and SYNTHETIC_MARKER in publish
        and "公開してもよいですか？" in publish
        and "正確に「公開して」と答えるまで" in publish
        and "「公開して」の後だけ" in publish
        and all(marker in publish for marker in (".env", "認証情報", "トークン", "個人情報", "顧客情報"))
        and "mightylink-app.com" not in publish
        and SYNTHETIC_MARKER in brief
        and "実在する顧客、社員、申込情報を含まない" in brief
    )

    forbidden_runtime = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage")
    filter_buttons = [button for button in parser.buttons if "data-filter" in button]
    select_buttons = [button for button in parser.buttons if "select-button" in button.get("class", "")]
    compact_css = re.sub(r"\s+", " ", css)
    h10 = (
        not parser.external_refs
        and all((files["output_dir"] / ref).is_file() for ref in parser.local_refs if not ref.startswith("mailto:"))
        and not any(marker in javascript for marker in forbidden_runtime)
        and "form" not in parser.tags
        and files["hero_image"].stat().st_size > 100_000
        and parser.headings == {"h1": 1, "h2": 3, "h3": 4}
        and len(filter_buttons) == 5
        and len(select_buttons) == 4
        and all("aria-pressed" in button for button in parser.buttons)
        and '@media (max-width: 640px)' in compact_css
        and "90秒以上進展が見えない" in readme
        and backup.count("行わないでください") == 3
        and "ローカル予備成果物" in _read_text(files["output_readme"])
    )

    hypotheses = [
        ("H1_six_stage_story", h1, "six prompts are ordered from grilling through publishing"),
        ("H2_grill_before_build", h2, "/grill-me asks one question at a time and cannot modify files"),
        ("H3_skill_discovery_quality", h3, "/find-skills compares provenance, adoption, audits, and install commands"),
        ("H4_build_boundary", h4, "build creates HTML/CSS only and verifies two viewports"),
        ("H5_steering_contract", h5, "Steering separates changes, preserved behavior, and measurable verification"),
        ("H6_skill_explanation", h6, "Skills and the two demonstrated skills are defined with a verified candidate"),
        ("H7_mcp_read_only", h7, "GitHub MCP is read-only and optional with a no-auth fallback"),
        ("H8_power_clarity", h8, "Power is explicitly training shorthand rather than an official feature"),
        ("H9_publish_safety", h9, "dedicated repository, synthetic data, secret checks, and exact approval are enforced"),
        ("H10_offline_accessible_recovery", h10, f"external_refs={len(parser.external_refs)}; headings={parser.headings}"),
    ]
    return [
        {"name": name, "path": files["readme"], "passed": passed, "detail": detail}
        for name, passed, detail in hypotheses
    ]


def collect_demo_kit_status(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    workshop = project_root / "docs" / "demo" / "antigravity_workshop"
    output = workshop / "output"
    files = {
        **{f"prompt{number}": workshop / f"PROMPT_{number:02d}_{suffix}.txt" for number, suffix in enumerate((
            "GRILL_ME", "FIND_SKILLS", "BUILD", "STEER", "MCP_CHECK", "PUBLISH"
        ))},
        "concepts": workshop / "DEMO_CONCEPTS.md",
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
    print("Google Antigravity 8/26 スキル活用ライブデモ検証")
    print("=" * 60)
    for check in result["checks"]:
        status = "OK" if check["passed"] else "FAIL"
        path = Path(check["path"])
        try:
            display_path = path.relative_to(project_root)
        except ValueError:
            display_path = path
        print(f"[{status}] {check['name']}: {display_path} ({check['detail']})")
    message = "\n[PASS] 要件整理、Skill検索、Steering、MCP読取、人の承認、専用Pages公開を安全に実演できます。"
    if not result["passed"]:
        message = "\n[FAIL] デモキットの不足を修正してください。"
    print(message)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(verify_demo_data())
