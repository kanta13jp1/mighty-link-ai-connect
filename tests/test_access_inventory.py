"""T850_1 access/ownership inventory audit tests."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_access_inventory as audit


def test_all_hypotheses_pass_on_real_inventory():
    report = audit.build_report("2026-07-08")
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["hypotheses_total"] == 10
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["status"] == "ok"


def test_required_critical_systems_present():
    rows = audit.load_inventory()
    ids = {r["system_id"] for r in rows}
    assert audit.REQUIRED_CRITICAL.issubset(ids)


def test_break_glass_docs_all_exist():
    rows = audit.load_inventory()
    refs = {r["break_glass_doc"].strip() for r in rows if r["break_glass_doc"].strip()}
    missing = [d for d in refs if not (PROJECT_ROOT / d).exists()]
    assert missing == [], f"missing break-glass docs: {missing}"


def test_spof_detection_reports_current_gaps():
    # The current pre-migration inventory has known bus-factor-1 criticals; the
    # audit must surface them (a regression that hides them would be dangerous).
    report = audit.build_report("2026-07-08")
    assert report["summary"]["spof_count"] >= 1
    assert "supabase" in report["summary"]["spof_systems"]


def test_spof_clears_when_backup_owner_set(tmp_path, monkeypatch):
    # If every critical system had a backup owner, SPOF count would be 0.
    rows = audit.load_inventory()
    for r in rows:
        if r["criticality"] == "critical" and not r["backup_owner"].strip():
            r["backup_owner"] = "会社管理者2"
    monkeypatch.setattr(audit, "load_inventory", lambda: rows)
    report = audit.build_report("2026-07-08")
    assert report["summary"]["spof_count"] == 0
    # H7 (SPOF detection) then legitimately fails to "detect" any — that is the
    # goal state, so verify the count path rather than H7's presence assertion.


def test_inventory_integrity_columns_and_ids():
    rows = audit.load_inventory()
    ids = [r["system_id"] for r in rows]
    assert len(ids) == len(set(ids))
    header = audit.INVENTORY.read_text(encoding="utf-8").split("\n")[0].split("\t")
    assert len(header) == 12


def test_secret_bearing_systems_linked_to_recovery_doc():
    rows = audit.load_inventory()
    for r in rows:
        if r["secret_bearing"].strip().lower() == "yes":
            assert r["break_glass_doc"].strip(), f"{r['system_id']} lacks a recovery/rotation doc"
