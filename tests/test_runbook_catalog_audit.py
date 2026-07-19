"""T902 test spec (written test-first): operations runbook catalog guard.

UAT TS-32 (docs/UAT_TEST_SPECIFICATION.md): there are 46 operational runbooks
(docs/*RUNBOOK*.md) but no index, so during an incident an operator cannot find
the right one, and a newly added runbook can silently escape discovery. This
suite pins the guard's pure functions: the on-disk runbook set is enumerated,
the runbooks linked from the catalog are parsed, and the two set differences —
orphan (on disk, not in catalog) and dangling (in catalog, not on disk) — are
computed. The catalog must also expose category headings.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_runbook_catalog as guard  # noqa: E402

SAMPLE_CATALOG = """# 運用Runbookカタログ

## DB・データ基盤
- [Supabase バックアップ・リストア](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) — 目的 — いつ開くか

## インフラ・監視・インシデント
- [本番死活監視・アラート](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md) — 目的 — いつ開くか
"""


def test_runbook_files_enumerates_disk_runbooks():
    files = guard.runbook_files()
    assert isinstance(files, set)
    assert len(files) >= 40, f"expected the full runbook corpus, got {len(files)}"
    assert all(name.endswith("RUNBOOK.md") or "RUNBOOK" in name for name in files)


def test_cataloged_runbooks_parses_markdown_links():
    got = guard.cataloged_runbooks(SAMPLE_CATALOG)
    assert got == {
        "SUPABASE_BACKUP_RESTORE_RUNBOOK.md",
        "UPTIME_MONITORING_AND_ALERT_RUNBOOK.md",
    }


def test_orphans_are_disk_runbooks_missing_from_catalog():
    files = {"A_RUNBOOK.md", "B_RUNBOOK.md", "C_RUNBOOK.md"}
    cataloged = {"A_RUNBOOK.md"}
    assert guard.orphan_runbooks(files, cataloged) == {"B_RUNBOOK.md", "C_RUNBOOK.md"}


def test_dangling_are_catalog_entries_missing_from_disk():
    files = {"A_RUNBOOK.md"}
    cataloged = {"A_RUNBOOK.md", "GONE_RUNBOOK.md"}
    assert guard.dangling_entries(files, cataloged) == {"GONE_RUNBOOK.md"}


def test_no_orphan_or_dangling_when_sets_match():
    files = {"A_RUNBOOK.md", "B_RUNBOOK.md"}
    cataloged = {"A_RUNBOOK.md", "B_RUNBOOK.md"}
    assert guard.orphan_runbooks(files, cataloged) == set()
    assert guard.dangling_entries(files, cataloged) == set()


def test_catalog_categories_reads_section_headings():
    cats = guard.catalog_categories(SAMPLE_CATALOG)
    assert "DB・データ基盤" in cats
    assert "インフラ・監視・インシデント" in cats
    assert "運用Runbookカタログ" not in cats, "the H1 title is not a category"


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"runbook-catalog hypotheses failing on real repo: {failed}"
