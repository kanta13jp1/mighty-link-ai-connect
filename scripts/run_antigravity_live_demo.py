#!/usr/bin/env python3
"""Fail closed unless the Antigravity AI-agent learning demo is ready."""

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
PROMPT_SUFFIXES = (
    "GRILL_ME",
    "FIND_SKILLS",
    "INSTALL_SKILL",
    "BUILD",
    "APPLY_SKILL",
    "MCP_CHECK",
    "PUBLISH",
)


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
    prompts = [_read_text(files[f"prompt{number}"]) for number in range(7)]
    grill, find_skills, install, build, apply_skill, mcp, publish = prompts
    concepts = _read_text(files["concepts"])
    backup = _read_text(files["backup"])
    readme = _read_text(files["readme"])
    brief = _read_text(files["site_brief"])
    html = _read_text(files["output_html"])
    css = _read_text(files["output_css"])
    javascript = _read_text(files["output_js"])
    cli_prompt = _read_text(files["prompt_cli"])
    sdk_prompt = _read_text(files["prompt_sdk"])
    sdk_script = _read_text(files["sdk_script"])

    parser = _SiteParser()
    parser.feed(html)

    h1 = (
        all(prompt.startswith(f"Prompt {number} /") for number, prompt in enumerate(prompts))
        and all(f"PROMPT_{number:02d}_{suffix}.txt" in readme for number, suffix in enumerate(PROMPT_SUFFIXES))
        and "30分" in readme
        and "残り30分" in readme
        and all(surface in readme for surface in ("Antigravity 2.0", "Antigravity CLI", "Antigravity SDK"))
        and "PROMPT_10_CLI_READONLY.txt" in readme
        and "PROMPT_11_SDK_READONLY.txt" in readme
    )

    h2 = all(
        marker in grill
        for marker in (
            "/grill-me",
            "最大2問",
            "1問ずつ質問",
            "推奨回答",
            "私の回答を待って",
            "決定事項／見送ること／停止条件／成功条件",
            "ファイル変更、コマンド実行、外部通信を行わない",
        )
    )

    h3 = all(
        marker in find_skills
        for marker in (
            "/find-skills",
            'npx skills find "frontend design"',
            "インストール数",
            "公開元とGitHub stars",
            "セキュリティ監査",
            "まだSkillのインストール",
        )
    )

    h4 = all(
        marker in install
        for marker in (
            "anthropics/skills@frontend-design",
            "--agent antigravity",
            "--copy -y",
            "npx skills list --json",
            ".agents/skills/frontend-design/SKILL.md",
            "index.html、styles.css、app.js、GitHub設定を変更せず",
        )
    ) and " -g" not in install

    h5 = all(
        marker in build
        for marker in (
            "@SITE_BRIEF.md",
            "index.htmlとstyles.css",
            "Codex、Claude Code、Claude Cowork、Kiro、Antigravity",
            "この初版ではJavaScript",
            "commitとpushは実行しない",
            "1440x900と390x844",
        )
    )

    h6 = all(
        marker in apply_skill
        for marker in (
            "/frontend-design",
            "最大2製品",
            "aria-live",
            "aria-pressed",
            "5・4・1・5",
            "SteeringとPowersを、Kiro固有の正式機能",
            "1440x900と390x844",
        )
    )

    h7 = all(
        marker in concepts
        for marker in (
            "## 主要機能マトリックス",
            "## Steering",
            "## Skills",
            "## Powers",
            "## MCP",
            "`Steering`はKiroの正式機能名です",
            "`Powers`はKiroの正式機能です",
            "Codex",
            "Claude Code",
            "Claude Cowork",
            "Antigravity",
            "anthropics/skills@frontend-design",
        )
    ) and all(
        marker in brief
        for marker in (
            "Specs、Steering、Hooks、Agent Skills、Powers、MCP",
            "Artifacts、Planning、Browser、Rules、Workflows、Skills、MCP",
        )
    )

    h8 = all(
        marker in mcp
        for marker in (
            "MCP Servers",
            "GitHub MCP",
            "読み取り専用",
            "Issue作成、設定変更、認証追加、ファイル変更、commit、pushは行わない",
            "MCP確認は省略、gitと公開URL確認へ継続",
        )
    ) and all(marker in concepts for marker in ("## MCP", "Model Context Protocol", "標準")) and all(
        marker in cli_prompt
        for marker in (
            "CLI DEMO / READ ONLY",
            "ファイルの作成、変更、削除をしない",
            "shell command、外部通信、commit、pushを実行しない",
            "SURFACE: ANTIGRAVITY CLI",
            "SYNTHETIC_DATA_ONLY",
        )
    ) and all(
        marker in sdk_prompt
        for marker in (
            "SDK DEMO / READ ONLY",
            "ファイルの作成、変更、削除、shell command、外部通信、git操作を行わない",
            "NOT_VERIFIED",
        )
    ) and all(
        marker in sdk_script
        for marker in (
            "BuiltinTools.read_only()",
            "MODE: READ ONLY",
            "--dry-run",
            "Never create, edit, or delete files",
            "GEMINI_API_KEY is not configured",
        )
    )

    h9 = (
        PAGES_REPOSITORY in publish
        and PAGES_URL in publish
        and "remoteまたはbranchが一致しなければ何も変更せず停止" in publish
        and SYNTHETIC_MARKER in publish
        and "公開してもよいですか？" in publish
        and "正確に「公開して」と答えるまで" in publish
        and "「公開して」の後だけ" in publish
        and ".agents/skills/`は公開対象へaddしない" in publish
        and all(marker in publish for marker in (".env", "認証情報", "トークン", "個人情報", "顧客情報"))
        and "mightylink-app.com" not in publish
        and SYNTHETIC_MARKER in brief
        and "実在する顧客、社員、申込情報、認証情報を含まない" in brief
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
        and parser.headings == {"h1": 1, "h2": 5, "h3": 5}
        and len(filter_buttons) == 4
        and len(select_buttons) == 5
        and all("aria-pressed" in button for button in parser.buttons)
        and '@media (max-width: 640px)' in compact_css
        and "selectedAgents.size >= 2" in javascript
        and "90秒以上" in readme
        and backup.count("行わないでください") == 4
        and "ローカル予備成果物" in _read_text(files["output_readme"])
    )

    hypotheses = [
        ("H1_three_surface_30min_story", h1, "IDE, CLI, and SDK fit a 30-minute demo with reserve time"),
        ("H2_grill_timeboxed", h2, "/grill-me asks at most two consequential questions and cannot modify files"),
        ("H3_skill_discovery_quality", h3, "/find-skills compares provenance, adoption, audits, and install commands"),
        ("H4_project_scoped_install", h4, "frontend-design installs only to the Antigravity demo repository"),
        ("H5_build_boundary", h5, "the first build is a five-agent HTML/CSS site without publishing"),
        ("H6_skill_application", h6, "the installed skill visibly improves design and two-agent comparison"),
        ("H7_product_feature_accuracy", h7, "the five products use official feature names and Kiro owns Steering/Powers"),
        ("H8_read_only_integrations", h8, "MCP, CLI, and SDK are read-only with no-auth fallbacks"),
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
        **{
            f"prompt{number}": workshop / f"PROMPT_{number:02d}_{suffix}.txt"
            for number, suffix in enumerate(PROMPT_SUFFIXES)
        },
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
        "prompt_cli": workshop / "PROMPT_10_CLI_READONLY.txt",
        "prompt_sdk": workshop / "PROMPT_11_SDK_READONLY.txt",
        "sdk_script": workshop / "antigravity_sdk_readonly.py",
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
    print("Antigravity AIエージェント学習サイト ライブデモ検証")
    print("=" * 60)
    for check in result["checks"]:
        status = "OK" if check["passed"] else "FAIL"
        path = Path(check["path"])
        try:
            display_path = path.relative_to(project_root)
        except ValueError:
            display_path = path
        print(f"[{status}] {check['name']}: {display_path} ({check['detail']})")
    message = "\n[PASS] 比較、Skill検索・導入、初版、改善、MCP、人の承認、Pages公開を安全に実演できます。"
    if not result["passed"]:
        message = "\n[FAIL] デモキットの不足を修正してください。"
    print(message)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(verify_demo_data())
