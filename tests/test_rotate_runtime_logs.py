import gzip
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import rotate_runtime_logs as rotate


def set_mtime(path: Path, timestamp: float) -> None:
    os.utime(path, (timestamp, timestamp))


def test_dry_run_reports_candidates_without_modifying_files(tmp_path):
    log_dir = tmp_path / "data" / "audit"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "ai_audit.jsonl"
    log_file.write_text('{"ok": true}\n', encoding="utf-8")
    now = datetime(2026, 6, 14, tzinfo=timezone.utc)
    set_mtime(log_file, now.timestamp() - (8 * 86400))

    report_path = tmp_path / "exports" / "report.json"
    exit_code = rotate.main(
        [
            "--root",
            str(tmp_path),
            "--report-path",
            str(report_path),
            "--dry-run",
            "--min-age-days",
            "7",
        ]
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert log_file.exists()
    assert report["dry_run"] is True
    assert report["candidates"][0]["source"] == "data\\audit\\ai_audit.jsonl" or report["candidates"][0]["source"] == "data/audit/ai_audit.jsonl"
    assert report["rotated_archives"] == []


def test_real_run_compresses_old_log_and_removes_source(tmp_path):
    log_dir = tmp_path / "data" / "audit"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "ai_audit.jsonl"
    log_file.write_text("line 1\nline 2\n", encoding="utf-8")
    set_mtime(log_file, datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())

    exit_code = rotate.main(
        [
            "--root",
            str(tmp_path),
            "--archive-dir",
            "data/log_archive",
            "--report-path",
            str(tmp_path / "report.json"),
            "--min-age-days",
            "1",
        ]
    )
    archives = list((tmp_path / "data" / "log_archive").rglob("*.gz"))

    assert exit_code == 0
    assert not log_file.exists()
    assert len(archives) == 1
    with gzip.open(archives[0], "rt", encoding="utf-8") as fh:
        assert fh.read() == "line 1\nline 2\n"


def test_prune_archives_respects_retention_days(tmp_path):
    archive_dir = tmp_path / "data" / "log_archive" / "2026" / "05"
    archive_dir.mkdir(parents=True)
    stale = archive_dir / "old.log.20260501T000000Z.gz"
    current = archive_dir / "new.log.20260614T000000Z.gz"
    stale.write_bytes(b"old")
    current.write_bytes(b"new")
    now = datetime(2026, 6, 14, tzinfo=timezone.utc)
    set_mtime(stale, now.timestamp() - (91 * 86400))
    set_mtime(current, now.timestamp() - (5 * 86400))

    pruned = rotate.prune_archives(
        root=tmp_path,
        archive_dir=tmp_path / "data" / "log_archive",
        retention_days=90,
        dry_run=False,
        now=now,
    )

    assert pruned == [str(stale.relative_to(tmp_path))]
    assert not stale.exists()
    assert current.exists()
