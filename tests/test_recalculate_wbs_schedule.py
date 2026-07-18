"""T897 test spec (written test-first): WBS forward-reschedule CLI guard.

The Antigravity lane drafted scripts/recalculate_wbs_schedule.py to pull WBS
schedules forward, but the draft had four defects the Claude Code review lane
must pin down so they can never regress (UAT: docs/UAT_TEST_SPECIFICATION.md
TS-23):

* hardcoded base date instead of the execution date,
* CRLF WBS.tsv rewritten with LF line endings (tracker TSV rule violation),
* docs/WBS.md regenerated in a format that conflicts with generate_wbs_md.py,
* implicit invocation from sync_wbs_to_sheets.py mutating the source of truth
  during a sync.

These tests define the reviewed contract: dry-run by default and no file
writes, apply moves only uncompleted stale rows to the base date preserving
duration and CRLF, completed rows and future-dated rows are never touched, and
the Sheets sync never imports or calls the recalculation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import recalculate_wbs_schedule as recalc  # noqa: E402

HEADER = (
    "タスクID\t大フェーズ\t小フェーズ\tタスク名\t担当\t実行エンジン\t"
    "Sheets Live 連携アクション\tステータス\t開始日\t終了予定日"
)

ROWS = [
    "T001\t1. 企画・設計\t要件定義\t完了済みタスク\t人間\tGemini\t-\t完了\t2026-05-20\t2026-05-21",
    "T002\t8. 本番運用・品質管理\t運用\t期限切れ未着手タスク\t人間\tCodex\t-\t未着手\t2026-07-10\t2026-07-12",
    "T003\t8. 本番運用・品質管理\t運用\t期限切れ実行中タスク\t人間\tCodex\t-\t実行中\t2026-07-13\t2026-07-15",
    "T004\t9. 長期保守・拡張\t保守\t将来予定タスク\t人間\tCodex\t-\t未着手\t2026-07-25\t2026-07-26",
    "T005\t1. 企画・設計\t要件定義\t日付が過去の完了タスク\t人間\tGemini\t-\t完了\t2026-07-01\t2026-07-02",
]

TODAY = "2026-07-18"


def write_fixture(path: Path) -> bytes:
    payload = ("\r\n".join([HEADER] + ROWS) + "\r\n").encode("utf-8")
    path.write_bytes(payload)
    return payload


def run(path: Path, *args: str) -> int:
    return recalc.main(["--wbs", str(path), "--today", TODAY, *args])


def read_rows(path: Path) -> dict[str, list[str]]:
    lines = path.read_bytes().decode("utf-8").splitlines()
    return {line.split("\t")[0]: line.split("\t") for line in lines[1:] if line.strip()}


# --------------------------------------------------------------------------- #
# Dry-run safety
# --------------------------------------------------------------------------- #
def test_dry_run_is_default_and_writes_nothing(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    original = write_fixture(tsv)
    assert run(tsv) == 0
    assert tsv.read_bytes() == original


def test_explicit_dry_run_writes_nothing(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    original = write_fixture(tsv)
    assert run(tsv, "--dry-run") == 0
    assert tsv.read_bytes() == original


# --------------------------------------------------------------------------- #
# Apply semantics
# --------------------------------------------------------------------------- #
def test_apply_moves_stale_uncompleted_rows_to_today(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    rows = read_rows(tsv)
    # Stale rows re-anchored to the base date, duration preserved (2 days).
    assert rows["T002"][8] == "2026-07-18"
    assert rows["T002"][9] == "2026-07-20"
    assert rows["T003"][8] == "2026-07-18"
    assert rows["T003"][9] == "2026-07-20"


def test_apply_never_touches_completed_rows(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    rows = read_rows(tsv)
    assert rows["T001"][8:10] == ["2026-05-20", "2026-05-21"]
    assert rows["T005"][8:10] == ["2026-07-01", "2026-07-02"]


def test_apply_leaves_future_rows_untouched(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    rows = read_rows(tsv)
    # Future-dated plans (fixed meetings, gated decisions) must not move.
    assert rows["T004"][8:10] == ["2026-07-25", "2026-07-26"]


def test_apply_keeps_no_backward_dates(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    for parts in read_rows(tsv).values():
        assert parts[8] <= parts[9]


def test_apply_is_idempotent(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    first = tsv.read_bytes()
    assert run(tsv, "--apply") == 0
    assert tsv.read_bytes() == first


# --------------------------------------------------------------------------- #
# File integrity (tracker TSV rules: UTF-8 / CRLF / 10 columns / unique IDs)
# --------------------------------------------------------------------------- #
def test_apply_preserves_crlf_and_column_count(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    write_fixture(tsv)
    assert run(tsv, "--apply") == 0
    raw = tsv.read_bytes().decode("utf-8")
    assert raw.count("\n") == raw.count("\r\n"), "CRLF must be preserved"
    lines = [line for line in raw.splitlines() if line.strip()]
    assert all(len(line.split("\t")) == 10 for line in lines)


def test_load_rejects_malformed_column_count(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    tsv.write_bytes(("\r\n".join([HEADER, "T900\tbroken row"]) + "\r\n").encode("utf-8"))
    assert run(tsv, "--apply") != 0


def test_load_rejects_duplicate_ids(tmp_path):
    tsv = tmp_path / "WBS.tsv"
    dup = ROWS + [ROWS[1]]
    tsv.write_bytes(("\r\n".join([HEADER] + dup) + "\r\n").encode("utf-8"))
    assert run(tsv, "--apply") != 0


# --------------------------------------------------------------------------- #
# Lane rule: the Sheets sync must never mutate the WBS source of truth
# --------------------------------------------------------------------------- #
def test_sheets_sync_does_not_invoke_recalculation():
    source = (PROJECT_ROOT / "scripts" / "sync_wbs_to_sheets.py").read_text(
        encoding="utf-8"
    )
    assert "recalculate_wbs_schedule" not in source
    assert "recalculate_wbs" not in source
