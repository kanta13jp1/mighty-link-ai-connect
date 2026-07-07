"""Audit Gemini model IDs against the project policy.

The audit keeps production model changes explicit:

* src/app.py must default to the policy production model.
* Runtime code must not use deprecated models or hot-swapped latest aliases.
* Current-truth docs/data must not describe an old model as the current default.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "data" / "gemini_model_policy.json"
DEFAULT_EXPORT_JSON = PROJECT_ROOT / "exports" / "gemini_model_policy_audit.json"
DEFAULT_EXPORT_MD = PROJECT_ROOT / "exports" / "gemini_model_policy_audit.md"

MODEL_RE = re.compile(
    r"\bgemini-(?:\d[a-z0-9._-]*|[a-z]+(?:-[a-z]+)*-latest)\b",
    re.IGNORECASE,
)
DEFAULT_MODEL_RE = re.compile(
    r"GEMINI_MODEL\s*=\s*os\.environ\.get\(\s*['\"]GEMINI_MODEL['\"]\s*,\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", "__pycache__", "node_modules", ".venv", "venv"}
TEXT_EXTENSIONS = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_policy(policy_path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    return json.loads(policy_path.read_text(encoding="utf-8"))


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"AGENTS.md", "CLAUDE.md"}


def iter_files(root: Path, roots: Iterable[str], exclude: Iterable[str] = ()) -> Iterable[Path]:
    exclude_set = {Path(item).as_posix() for item in exclude}
    for item in roots:
        base = root / item
        if not base.exists():
            continue
        if base.is_file():
            if is_text_file(base):
                yield base
            continue
        for path in base.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if rel_path(path, root) in exclude_set:
                continue
            if path.is_file() and is_text_file(path):
                yield path


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def context_for(text: str, offset: int, radius: int = 90) -> str:
    start = max(0, offset - radius)
    end = min(len(text), offset + radius)
    return " ".join(text[start:end].split())


def collect_model_references(path: Path, root: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    references: list[dict[str, Any]] = []
    for match in MODEL_RE.finditer(text):
        references.append(
            {
                "path": rel_path(path, root),
                "line": line_for_offset(text, match.start()),
                "model": match.group(0).lower(),
                "context": context_for(text, match.start()),
            }
        )
    return references


def matches_any(patterns: Iterable[str], model: str) -> str | None:
    for pattern in patterns:
        if re.match(pattern, model):
            return pattern
    return None


def extract_app_default(root: Path) -> str | None:
    app_path = root / "src" / "app.py"
    if not app_path.exists():
        return None
    text = app_path.read_text(encoding="utf-8", errors="ignore")
    match = DEFAULT_MODEL_RE.search(text)
    if not match:
        return None
    return match.group(1).lower()


def classify_runtime_reference(ref: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any] | None:
    model = ref["model"]
    blocked_pattern = matches_any(policy["blocked_model_patterns"], model)
    stable = set(policy["stable_production_models"])
    evaluation_only = set(policy["evaluation_only_models"])

    if blocked_pattern:
        return {
            **ref,
            "severity": "blocker",
            "reason": f"blocked_by_pattern:{blocked_pattern}",
        }
    if model in stable:
        return {
            **ref,
            "severity": "ok",
            "reason": "stable_production_model",
        }
    if model in evaluation_only:
        return {
            **ref,
            "severity": "warning",
            "reason": "evaluation_only_model_in_runtime_path",
        }
    return {
        **ref,
        "severity": "blocker",
        "reason": "unknown_or_unapproved_model",
    }


def classify_current_truth_reference(ref: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any] | None:
    model = ref["model"]
    default = policy["production_default"]
    blocked_pattern = matches_any(policy["blocked_model_patterns"], model)
    markers = policy.get("current_truth_context_markers", [])
    non_current_markers = policy.get("current_truth_non_current_markers", [])
    context_lower = ref["context"].lower()
    marker_found = any(marker.lower() in context_lower for marker in markers)
    non_current_marker_found = any(marker.lower() in context_lower for marker in non_current_markers)

    if blocked_pattern:
        return {
            **ref,
            "severity": "blocker",
            "reason": f"current_truth_blocked_model:{blocked_pattern}",
        }
    if marker_found and model != default and not non_current_marker_found:
        return {
            **ref,
            "severity": "blocker",
            "reason": f"current_truth_model_mismatch:expected_{default}",
        }
    return {
        **ref,
        "severity": "ok",
        "reason": "current_truth_reference_allowed",
    }


def build_report(
    root: Path = PROJECT_ROOT,
    policy_path: Path = DEFAULT_POLICY_PATH,
    checked_at: str | None = None,
) -> dict[str, Any]:
    checked_at = checked_at or date.today().isoformat()
    policy = load_policy(policy_path)
    production_default = policy["production_default"]
    app_default = extract_app_default(root)

    default_finding: dict[str, Any]
    if app_default == production_default:
        default_finding = {
            "severity": "ok",
            "path": "src/app.py",
            "model": app_default,
            "reason": "app_default_matches_policy",
        }
    elif app_default is None:
        default_finding = {
            "severity": "blocker",
            "path": "src/app.py",
            "model": None,
            "reason": "app_default_not_found",
        }
    else:
        default_finding = {
            "severity": "blocker",
            "path": "src/app.py",
            "model": app_default,
            "reason": f"app_default_mismatch:expected_{production_default}",
        }

    runtime_findings = []
    for path in iter_files(root, policy.get("active_scan_roots", []), policy.get("scan_exclude_paths", [])):
        for ref in collect_model_references(path, root):
            finding = classify_runtime_reference(ref, policy)
            if finding:
                runtime_findings.append(finding)

    current_truth_findings = []
    for item in policy.get("current_truth_paths", []):
        path = root / item
        if not path.exists():
            current_truth_findings.append(
                {
                    "severity": "warning",
                    "path": item,
                    "model": None,
                    "reason": "current_truth_path_missing",
                }
            )
            continue
        for ref in collect_model_references(path, root):
            finding = classify_current_truth_reference(ref, policy)
            if finding:
                current_truth_findings.append(finding)

    blockers = [
        finding
        for finding in [default_finding, *runtime_findings, *current_truth_findings]
        if finding["severity"] == "blocker"
    ]
    warnings = [
        finding
        for finding in [default_finding, *runtime_findings, *current_truth_findings]
        if finding["severity"] == "warning"
    ]

    return {
        "audit": "gemini_model_policy",
        "status": "blocked" if blockers else "ok",
        "checked_at": checked_at,
        "policy": policy,
        "summary": {
            "production_default": production_default,
            "app_default": app_default,
            "blockers": len(blockers),
            "warnings": len(warnings),
            "runtime_references": len(runtime_findings),
            "current_truth_references": len(current_truth_findings),
        },
        "default_finding": default_finding,
        "runtime_findings": runtime_findings,
        "current_truth_findings": current_truth_findings,
        "blockers": blockers,
        "warnings": warnings,
    }


def write_json(report: dict[str, Any], output_path: Path = DEFAULT_EXPORT_JSON) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_markdown(report: dict[str, Any], output_path: Path = DEFAULT_EXPORT_MD) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gemini Model Policy Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Checked at: {report['checked_at']}",
        f"- Production default: `{report['summary']['production_default']}`",
        f"- App default: `{report['summary']['app_default']}`",
        f"- Blockers: {report['summary']['blockers']}",
        f"- Warnings: {report['summary']['warnings']}",
        "",
        "## Official Docs Snapshot",
        "",
        f"- Models: {report['policy']['official_docs']['models_url']}",
        f"- Context caching: {report['policy']['official_docs']['context_caching_url']}",
        f"- Models page last updated UTC: {report['policy']['official_docs']['models_last_updated_utc']}",
        "",
        "## Blockers",
        "",
    ]

    if report["blockers"]:
        lines.append("| Path | Line | Model | Reason |")
        lines.append("| --- | ---: | --- | --- |")
        for finding in report["blockers"]:
            lines.append(
                f"| {finding.get('path')} | {finding.get('line', '')} | "
                f"`{finding.get('model')}` | {finding.get('reason')} |"
            )
    else:
        lines.append("No blockers.")

    lines.extend(["", "## Runtime References", "", "| Path | Line | Model | Severity | Reason |", "| --- | ---: | --- | --- | --- |"])
    for finding in report["runtime_findings"]:
        lines.append(
            f"| {finding['path']} | {finding['line']} | `{finding['model']}` | "
            f"{finding['severity']} | {finding['reason']} |"
        )

    lines.extend(["", "## Current Truth References", "", "| Path | Line | Model | Severity | Reason |", "| --- | ---: | --- | --- | --- |"])
    for finding in report["current_truth_findings"]:
        lines.append(
            f"| {finding['path']} | {finding['line']} | `{finding['model']}` | "
            f"{finding['severity']} | {finding['reason']} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Gemini model usage against data/gemini_model_policy.json.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--checked-at", default=None)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_EXPORT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_EXPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root, args.policy, args.checked_at)
    json_path = write_json(report, args.json_output)
    markdown_path = write_markdown(report, args.markdown_output)

    print(f"[*] Wrote {json_path}")
    print(f"[*] Wrote {markdown_path}")
    if report["status"] != "ok":
        print(f"[-] Gemini model policy audit blocked: {report['summary']['blockers']} blocker(s)")
        return 1
    print("[+] Gemini model policy audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
