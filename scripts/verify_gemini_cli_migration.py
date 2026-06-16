#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Verify that the repo no longer depends on deprecated Gemini CLI surfaces.

WBS T803 covers the 2026-06-18 shutdown of Gemini CLI / Gemini Code Assist
requests for individual accounts, plus the Firebase extension for Gemini CLI.
The repo may keep historical documentation about the migration, but active
scripts, CI, source code, and operational config must not require those tools.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "exports"
MAX_TEXT_FILE_BYTES = 1_500_000


@dataclass(frozen=True)
class DeprecatedPattern:
    key: str
    label: str
    regex: re.Pattern[str]
    replacement: str


DEPRECATED_PATTERNS = (
    DeprecatedPattern(
        key="gemini_cli_firebase_extension",
        label="Firebase extension for Gemini CLI",
        regex=re.compile(
            r"\bgemini(?:\.cmd|\.exe)?\s+extensions\s+(?:install|update|enable|disable)\b.*"
            r"(?:firebase|agent-skills|gcli-extension)",
            re.IGNORECASE,
        ),
        replacement="Use Antigravity CLI / Antigravity agent skills directly; do not install Firebase skills through Gemini CLI.",
    ),
    DeprecatedPattern(
        key="firebase_agent_skills_gemini_cli",
        label="Firebase agent skills through Gemini CLI",
        regex=re.compile(r"(?:github\.com/)?firebase/agent-skills|gcli-extension", re.IGNORECASE),
        replacement="Install Firebase agent skills through the supported Antigravity path, not through Gemini CLI extensions.",
    ),
    DeprecatedPattern(
        key="gemini_cli_command",
        label="Gemini CLI command",
        regex=re.compile(
            r"(?<![A-Za-z0-9_-])gemini(?:\.cmd|\.exe)?\s+"
            r"(?:auth|chat|extensions|login|mcp|run|serve|tunnel|--help|-h)\b",
            re.IGNORECASE,
        ),
        replacement="Use antigravity-ide.cmd / Antigravity CLI for the Google agent lane.",
    ),
    DeprecatedPattern(
        key="gemini_code_assist_extension",
        label="Gemini Code Assist IDE extension",
        regex=re.compile(r"google\.geminicodeassist|gemini[-_\s]+code[-_\s]+assist", re.IGNORECASE),
        replacement="Use Antigravity IDE/CLI for individual Google agent workflows; enterprise GCA is separate.",
    ),
    DeprecatedPattern(
        key="gemini_cli_name",
        label="Gemini CLI named dependency",
        regex=re.compile(r"\bGemini CLI\b", re.IGNORECASE),
        replacement="Keep only historical migration notes; active setup must say Antigravity CLI.",
    ),
)


OFFICIAL_SOURCES = (
    {
        "title": "Google Developers Blog: Transitioning Gemini CLI to Antigravity CLI",
        "url": "https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/",
        "finding": "Gemini CLI / Gemini Code Assist individual requests stop on 2026-06-18; Antigravity CLI is the replacement lane.",
    },
    {
        "title": "Gemini Code Assist for individuals",
        "url": "https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals",
        "finding": "Consumer/individual Gemini Code Assist and Gemini CLI requests stop on 2026-06-18; standard and enterprise tiers are not impacted.",
    },
    {
        "title": "Firebase extension for Gemini CLI",
        "url": "https://firebase.google.com/docs/ai-assistance/gcli-extension",
        "finding": "The Firebase extension for Gemini CLI stops working on 2026-06-18; migrate Firebase agent work to Antigravity CLI.",
    },
    {
        "title": "Firebase release notes",
        "url": "https://firebase.google.com/support/release-notes",
        "finding": "Firebase repeats the 2026-06-18 Gemini CLI extension shutdown and directs users to Antigravity CLI / direct Firebase agent skills.",
    },
    {
        "title": "Gemini API model docs",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "finding": "Gemini API model usage remains separate from deprecated Gemini CLI tooling.",
    },
)


OPERATIONAL_ROOTS = {
    ".github",
    ".vscode",
    "db",
    "functions",
    "scripts",
    "src",
    "supabase",
}

ROOT_OPERATIONAL_FILES = {
    ".firebaserc",
    "AGENTS.md",
    "CLAUDE.md",
    "firebase.json",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "README.md",
    "requirements.txt",
    "yarn.lock",
}

AUDIT_TOOL_FILES = {
    "docs/GEMINI_CLI_MIGRATION_AUDIT_2026-06-17.md",
    "exports/gemini_cli_migration_audit.json",
    "exports/gemini_cli_migration_audit.md",
    "scripts/verify_gemini_cli_migration.py",
    "tests/test_gemini_cli_migration.py",
}

REFERENCE_ROOTS = {"docs"}
REFERENCE_FILES = {"data/WBS.tsv", "exports/mighty_development_plan.ics"}
EXCLUDED_DIR_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_path(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def should_skip(path: Path, project_root: Path) -> bool:
    rel = path.relative_to(project_root)
    parts = {part.lower() for part in rel.parts}
    if parts & EXCLUDED_DIR_PARTS:
        return True
    rel_posix = rel.as_posix()
    if rel_posix in AUDIT_TOOL_FILES:
        return True
    if path.stat().st_size > MAX_TEXT_FILE_BYTES:
        return True
    return False


def is_operational_path(path: Path, project_root: Path) -> bool:
    rel = path.relative_to(project_root)
    rel_posix = rel.as_posix()
    first = rel.parts[0] if rel.parts else ""
    if rel_posix in ROOT_OPERATIONAL_FILES:
        return True
    if first in OPERATIONAL_ROOTS:
        return True
    return False


def is_reference_path(path: Path, project_root: Path) -> bool:
    rel = path.relative_to(project_root)
    rel_posix = rel.as_posix()
    first = rel.parts[0] if rel.parts else ""
    if first in REFERENCE_ROOTS:
        return True
    if rel_posix in REFERENCE_FILES:
        return True
    return False


def read_text(path: Path) -> str | None:
    raw = path.read_bytes()
    if b"\0" in raw[:4096]:
        return None
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def scan_file(path: Path, project_root: Path, state: str) -> list[dict[str, Any]]:
    text = read_text(path)
    if text is None:
        return []

    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in DEPRECATED_PATTERNS:
            if not pattern.regex.search(line):
                continue
            findings.append(
                {
                    "state": state,
                    "severity": "critical" if state == "active_dependency" else "info",
                    "pattern": pattern.key,
                    "label": pattern.label,
                    "path": rel_path(path, project_root),
                    "line": line_number,
                    "evidence": line.strip()[:240],
                    "replacement": pattern.replacement,
                }
            )
    return findings


def iter_project_files(project_root: Path) -> list[Path]:
    return sorted(
        path
        for path in project_root.rglob("*")
        if path.is_file() and not should_skip(path, project_root)
    )


def command_check(command_names: list[str]) -> dict[str, Any]:
    for command in command_names:
        found = shutil.which(command)
        if found:
            return {"state": "available", "command": command, "path": found}
    return {"state": "not_found", "command": command_names[0], "path": None}


def build_report(project_root: Path, audit_date: str) -> dict[str, Any]:
    files = iter_project_files(project_root)
    active_findings: list[dict[str, Any]] = []
    reference_findings: list[dict[str, Any]] = []
    operational_files_scanned = 0
    reference_files_scanned = 0

    for path in files:
        if is_operational_path(path, project_root):
            operational_files_scanned += 1
            active_findings.extend(scan_file(path, project_root, "active_dependency"))
        elif is_reference_path(path, project_root):
            reference_files_scanned += 1
            reference_findings.extend(scan_file(path, project_root, "historical_reference"))

    antigravity = command_check(["antigravity-ide.cmd", "antigravity-ide"])
    gemini_cli = command_check(["gemini.cmd", "gemini"])
    if gemini_cli["state"] == "available":
        gemini_cli["state"] = "warning"
        gemini_cli["message"] = (
            "A local Gemini CLI executable is still on PATH, but no repo operational dependency was found. "
            "Do not use it for this project after 2026-06-18."
        )
    else:
        gemini_cli["message"] = "No local Gemini CLI executable was found on PATH."

    status = "critical" if active_findings else "ok"
    return {
        "status": status,
        "audit_date": audit_date,
        "generated_at": utc_now(),
        "official_sources": OFFICIAL_SOURCES,
        "summary": {
            "active_blockers": len(active_findings),
            "historical_references": len(reference_findings),
            "operational_files_scanned": operational_files_scanned,
            "reference_files_scanned": reference_files_scanned,
        },
        "tool_checks": {
            "antigravity_cli": {
                **antigravity,
                "message": "Antigravity CLI is available on PATH."
                if antigravity["state"] == "available"
                else "Antigravity CLI was not found on PATH in this shell; repo audit still completed.",
            },
            "gemini_cli": gemini_cli,
        },
        "active_findings": active_findings,
        "reference_findings": reference_findings,
        "guardrails": [
            "Do not add `gemini extensions install https://github.com/firebase/agent-skills/` to scripts, CI, or setup docs.",
            "Do not require `google.geminicodeassist` or the individual Gemini Code Assist IDE extension in .vscode recommendations.",
            "Use Antigravity CLI / Antigravity IDE for the Google agent lane; keep Gemini API usage as API/model integration only.",
            "Keep historical docs only when they explicitly describe the migration or shutdown context.",
        ],
    }


def write_json(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "gemini_cli_migration_audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gemini CLI / Code Assist 残存依存監査レポート",
        "",
        f"- 監査日: {report['audit_date']}",
        f"- 生成時刻(UTC): {report['generated_at']}",
        f"- 総合判定: **{report['status'].upper()}**",
        "",
        "## サマリー",
        "",
        f"- 実運用設定の残存依存: {report['summary']['active_blockers']} 件",
        f"- 実運用ファイルの走査数: {report['summary']['operational_files_scanned']} 件",
        f"- docs/WBS 等の履歴参照: {report['summary']['historical_references']} 件",
        f"- 履歴参照ファイルの走査数: {report['summary']['reference_files_scanned']} 件",
        "",
        "## 公式情報の確認結果",
        "",
    ]
    for source in report["official_sources"]:
        lines.append(f"- [{source['title']}]({source['url']}): {source['finding']}")

    lines.extend(
        [
            "",
            "## ツール確認",
            "",
        ]
    )
    for name, row in report["tool_checks"].items():
        path = row.get("path") or "-"
        lines.append(f"- {name}: {row['state']} ({path}) — {row['message']}")

    lines.extend(["", "## 実運用依存の検出結果", ""])
    if report["active_findings"]:
        lines.append("| パターン | ファイル | 行 | 対応 |")
        lines.append("| :--- | :--- | ---: | :--- |")
        for finding in report["active_findings"]:
            lines.append(
                f"| {finding['label']} | `{finding['path']}` | {finding['line']} | {finding['replacement']} |"
            )
    else:
        lines.append(
            "実運用ファイル（CI、scripts、src、Firebase/Supabase 設定、VSCode 推奨拡張、AGENTS.md 等）に、"
            "Gemini CLI / Gemini Code Assist / Firebase Gemini CLI 拡張への現役依存は見つかりませんでした。"
        )

    lines.extend(["", "## 履歴参照", ""])
    if report["reference_findings"]:
        lines.append(
            "docs/WBS/カレンダー成果物には移行経緯を説明する履歴参照が残っています。"
            "これらは実行依存ではなく、T693/T803 の証跡として保持します。"
        )
        lines.append("")
        lines.append("| 種別 | ファイル | 行 | 抜粋 |")
        lines.append("| :--- | :--- | ---: | :--- |")
        for finding in report["reference_findings"][:30]:
            evidence = finding["evidence"].replace("|", "\\|")
            lines.append(f"| {finding['label']} | `{finding['path']}` | {finding['line']} | {evidence} |")
        remaining = len(report["reference_findings"]) - 30
        if remaining > 0:
            lines.append(f"| ... | ... | ... | ほか {remaining} 件 |")
    else:
        lines.append("履歴参照は検出されませんでした。")

    lines.extend(
        [
            "",
            "## ガードレール",
            "",
        ]
    )
    for guardrail in report["guardrails"]:
        lines.append(f"- {guardrail}")
    lines.append("")
    return "\n".join(lines)


def write_markdown(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "gemini_cli_migration_audit.md"
    output.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()
    report = build_report(project_root, args.date)
    json_path = write_json(report, output_dir)
    md_path = write_markdown(report, output_dir)

    summary = report["summary"]
    print(
        "Gemini CLI migration audit: "
        f"{report['status']} "
        f"(active_blockers={summary['active_blockers']}, "
        f"historical_references={summary['historical_references']})"
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 1 if report["status"] == "critical" else 0


if __name__ == "__main__":
    raise SystemExit(main())
