"""GitHub issue ↔ WBS reconciliation (T849_3).

T849 (GAリリース閉鎖) requires "GitHub Issues/Project 未完了0". But
`sync_wbs_to_github.py` is deliberately targeted — it is invoked per task
(`sync_wbs_to_github.py TXXX`) so it never touches the full historical WBS. The
consequence is that a lane which completes a task without running the sync
leaves its issue open indefinitely, and the closure criterion counts work that
is actually finished.

On 2026-07-20 that had produced two stale issues: #158 (T866) and #139 (T852),
both for tasks long since 完了.

This tool reconciles the two sides and reports:

* stale       — every WBS task the issue references is 完了 → close it
                (`python scripts/sync_wbs_to_github.py <TASKS>` does so via the
                project's own automation, keeping labels/Project state correct)
* legitimate  — at least one referenced task is still open → leave it
* unlinked    — no resolvable WBS task → never auto-closed, needs a human look

It requires `gh` and network, so it is NOT a preflight guard (registered in
EXEMPT_GUARDS); run it on demand, e.g. before a GA-closure judgement.

Output: exports/github_issue_wbs_sync_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WBS = PROJECT_ROOT / "data" / "WBS.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "github_issue_wbs_sync_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "github_issue_wbs_sync_audit.md"

# A WBS task id: T + digits, optionally _<digits> for a sub-task.
#
# \b cannot be used on the trailing side: Japanese is word-characters to Python's
# regex, so "T837完了" has NO boundary after the digits and the id would be missed
# (exactly how #162's "T811/T837完了" hid T837). Use explicit lookarounds instead —
# the trailing one excludes _ as well so "T798_1" is not truncated to "T798".
_TASK_RE = re.compile(r"(?<![A-Za-z0-9_])T(\d+)(_\d+)?(?![0-9_])")

DONE = "完了"


def extract_wbs_ids(text: str) -> set[str]:
    """WBS task ids referenced anywhere in the given text."""
    return {m.group(0) for m in _TASK_RE.finditer(text or "")}


def load_wbs_status(path: Path = WBS) -> dict[str, str]:
    """Map of task id -> ステータス from the WBS source of truth."""
    lines = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").split("\n")
    header = lines[0].split("\t")
    i_id, i_status = header.index("タスクID"), header.index("ステータス")
    status: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) > i_status:
            status[cells[i_id]] = cells[i_status]
    return status


def classify_open_issues(
    issues: list[dict[str, Any]], wbs_status: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    """Split open issues into stale / legitimate / unlinked.

    An issue is stale only when it references at least one KNOWN task and EVERY
    known task it references is 完了 — a mixed issue (some done, some open) is
    still tracking live work and must not be closed.
    """
    stale, legitimate, unlinked = [], [], []
    for issue in issues:
        text = f"{issue.get('title', '')}\n{issue.get('body', '') or ''}"
        known = {t for t in extract_wbs_ids(text) if t in wbs_status}
        record = dict(issue)
        record["wbs_tasks"] = sorted(known)
        if not known:
            unlinked.append(record)
        elif all(wbs_status[t] == DONE for t in known):
            stale.append(record)
        else:
            record["open_tasks"] = sorted(t for t in known if wbs_status[t] != DONE)
            legitimate.append(record)
    return {"stale": stale, "legitimate": legitimate, "unlinked": unlinked}


def fetch_open_issues(limit: int = 100) -> list[dict[str, Any]]:
    """Open issues via gh. Raises RuntimeError when gh/network is unavailable."""
    try:
        proc = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--limit", str(limit),
             "--json", "number,title,body,url"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"gh の実行に失敗しました: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue list が失敗しました: {(proc.stderr or '').strip()[:300]}")
    return json.loads(proc.stdout or "[]")


def render_markdown(report: dict[str, Any]) -> str:
    stale, legit = report["stale"], report["legitimate"]
    unlinked = report["unlinked"]
    lines = [
        "# GitHub Issue ↔ WBS 整合監査 (T849_3)",
        "",
        f"- open issue 総数: **{report['open_count']}**",
        f"- 要クローズ(参照WBSが全て完了): **{len(stale)}**",
        f"- 正当にopen(未完了WBSあり): **{len(legit)}**",
        f"- WBS未参照(人間確認): **{len(unlinked)}**",
        f"- 総合判定: {'✅ PASS (stale 0)' if not stale else '❌ FAIL (staleあり)'}",
        "",
    ]
    if stale:
        lines += ["## 要クローズ", "", "| Issue | タスク | タイトル |", "| --- | --- | --- |"]
        for i in stale:
            lines.append(f"| #{i['number']} | {', '.join(i['wbs_tasks'])} | {i.get('title','')[:70]} |")
        tasks = sorted({t for i in stale for t in i["wbs_tasks"]})
        lines += ["", "解消コマンド:", "",
                  f"```\npython scripts/sync_wbs_to_github.py {' '.join(tasks)}\n```", ""]
    if legit:
        lines += ["## 正当にopen", "", "| Issue | 未完了タスク | タイトル |", "| --- | --- | --- |"]
        for i in legit:
            lines.append(
                f"| #{i['number']} | {', '.join(i.get('open_tasks', []))} | {i.get('title','')[:70]} |")
        lines.append("")
    if unlinked:
        lines += ["## WBS未参照(自動クローズ対象外)", "", "| Issue | タイトル |", "| --- | --- |"]
        for i in unlinked:
            lines.append(f"| #{i['number']} | {i.get('title','')[:70]} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub Issue と WBS の整合監査 (T849_3)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    try:
        issues = fetch_open_issues()
    except RuntimeError as exc:
        print(f"[-] {exc}")
        print("[*] 本ツールは gh 認証とネットワークを必要とします(プリフライト対象外)。")
        return 2

    classified = classify_open_issues(issues, load_wbs_status())
    report = {"open_count": len(issues), **classified}

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_markdown(report)
    args.md.write_text(md, encoding="utf-8")
    print(md)
    return 0 if not classified["stale"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
