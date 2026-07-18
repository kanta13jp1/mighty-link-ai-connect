#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Mighty-Link AI Connect: WBS 前倒しスケジュール引き直し CLI (T897)

data/WBS.tsv の未完了タスク（未着手/実行中）のうち、開始日が基準日より過去に
取り残された行を基準日へ引き直す（所要日数は維持）。以下は変更しない:

* ステータス「完了」の行（履歴は不変）
* 開始日が基準日以降の行（定例・経営判断など日付が固定された将来タスクを
  一括で早める判断は人間が個別に行う。過去ラウンド T702_2 / T809 と同様）

安全規約（UAT: docs/UAT_TEST_SPECIFICATION.md TS-23 / tests/test_recalculate_wbs_schedule.py）:

* 既定は --dry-run。--apply を明示したときだけ書き込む。
* WBS.tsv は UTF-8 / CRLF / 10列 / タスクID一意を維持し、違反があれば書き込まずに失敗する。
* docs/WBS.md は正規ジェネレータ scripts/generate_wbs_md.py に委譲して再生成する。
* 本 CLI を sync_wbs_to_sheets.py 等から暗黙に呼び出してはならない（正本の暗黙変更禁止）。

初版ドラフト: Antigravity 2.0 / レビュー・安全化: Claude Code (T897)
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TSV = PROJECT_ROOT / "data" / "WBS.tsv"
GENERATOR = PROJECT_ROOT / "scripts" / "generate_wbs_md.py"

EXPECTED_COLUMNS = 10
STATUS_COL = 7
START_COL = 8
END_COL = 9
STATUS_DONE = "完了"


def parse_date(value: str) -> datetime.date | None:
    value = (value or "").strip()
    if value in ("", "-"):
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_wbs(path: Path) -> tuple[list[str], list[list[str]]]:
    """Load and validate the WBS TSV (10 columns, unique task IDs)."""
    raw = path.read_bytes().decode("utf-8")
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"WBS file is empty: {path}")

    header = lines[0].split("\t")
    if len(header) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Header has {len(header)} columns, expected {EXPECTED_COLUMNS}: {path}"
        )

    rows: list[list[str]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(lines[1:], start=2):
        parts = line.split("\t")
        if len(parts) != EXPECTED_COLUMNS:
            raise ValueError(
                f"Line {lineno}: {len(parts)} columns, expected {EXPECTED_COLUMNS}"
            )
        task_id = parts[0].strip()
        if task_id in seen:
            raise ValueError(f"Line {lineno}: duplicate task ID {task_id}")
        seen.add(task_id)
        rows.append(parts)
    return header, rows


def save_wbs(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write the TSV back as UTF-8 with CRLF line endings (tracker TSV rule)."""
    lines = ["\t".join(header)] + ["\t".join(row) for row in rows]
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))


def plan_reschedule(
    rows: list[list[str]], today: datetime.date
) -> list[dict[str, str]]:
    """Re-anchor stale uncompleted rows to `today`, preserving duration.

    Mutates `rows` in place and returns one change record per moved task.
    """
    changes: list[dict[str, str]] = []
    for row in rows:
        if row[STATUS_COL].strip() == STATUS_DONE:
            continue
        start = parse_date(row[START_COL])
        end = parse_date(row[END_COL])
        if start is None or end is None or start >= today:
            continue
        duration = max((end - start).days, 0)
        new_start = today
        new_end = today + datetime.timedelta(days=duration)
        changes.append(
            {
                "task_id": row[0].strip(),
                "name": row[3].strip(),
                "old_start": row[START_COL],
                "old_end": row[END_COL],
                "new_start": new_start.isoformat(),
                "new_end": new_end.isoformat(),
            }
        )
        row[START_COL] = new_start.isoformat()
        row[END_COL] = new_end.isoformat()
    return changes


def regenerate_wbs_md() -> None:
    subprocess.run([sys.executable, str(GENERATOR)], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-anchor stale uncompleted WBS tasks to a base date (default: dry-run).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview changes only (default)")
    mode.add_argument("--apply", action="store_true", help="Write changes to the TSV")
    parser.add_argument("--wbs", type=Path, default=DEFAULT_TSV, help="Path to WBS.tsv")
    parser.add_argument(
        "--today",
        type=str,
        default=None,
        help="Base date YYYY-MM-DD (default: the execution date)",
    )
    args = parser.parse_args(argv)

    today = parse_date(args.today) if args.today else datetime.date.today()
    if today is None:
        print(f"[-] Invalid --today value: {args.today}")
        return 1

    try:
        header, rows = load_wbs(args.wbs)
    except (OSError, ValueError) as exc:
        print(f"[-] Failed to load WBS: {exc}")
        return 1

    changes = plan_reschedule(rows, today)

    if not changes:
        print(f"[*] No stale uncompleted tasks before {today}; nothing to reschedule.")
        return 0

    print(f"[*] Base date: {today} / {len(changes)} task(s) to re-anchor:")
    for change in changes:
        print(
            f"    {change['task_id']}: {change['old_start']}..{change['old_end']}"
            f" -> {change['new_start']}..{change['new_end']}  {change['name']}"
        )

    if not args.apply:
        print("[*] Dry-run (default): no files were modified. Re-run with --apply to write.")
        return 0

    try:
        save_wbs(args.wbs, header, rows)
    except OSError as exc:
        print(f"[-] Failed to write WBS: {exc}")
        return 1
    print(f"[+] Updated {len(changes)} task(s) in {args.wbs}")

    if args.wbs.resolve() == DEFAULT_TSV.resolve():
        regenerate_wbs_md()
        print("[+] docs/WBS.md regenerated via scripts/generate_wbs_md.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
