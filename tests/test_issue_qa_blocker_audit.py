import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_issue_qa_blockers as audit


def test_build_report_flags_open_issue_and_unanswered_qa():
    report = audit.build_report(
        [
            {"ID": "R1", "状態": "resolved", "重要度": "LOW", "カテゴリ": "docs", "タイトル": "done"},
            {"ID": "R2", "状態": "open", "重要度": "HIGH", "カテゴリ": "ci", "タイトル": "needs work"},
        ],
        [
            {"ID": "QA-1", "状態": "回答済", "カテゴリ": "ops", "質問": "answered"},
            {"ID": "QA-2", "状態": "未回答", "カテゴリ": "ops", "質問": "pending"},
        ],
    )

    assert report["status"] == "blocked"
    assert report["issue_blocker_count"] == 1
    assert report["qa_blocker_count"] == 1
    assert report["issue_blockers"][0]["id"] == "R2"
    assert report["qa_blockers"][0]["id"] == "QA-2"


def test_build_report_accepts_transferred_and_answered_states():
    report = audit.build_report(
        [
            {"ID": "R1", "状態": "transferred", "重要度": "MED", "カテゴリ": "release"},
            {"ID": "R2", "状態": "accepted_non_blocker", "重要度": "LOW", "カテゴリ": "docs"},
            {"ID": "R3", "状態": "maintenance", "重要度": "LOW", "カテゴリ": "infra"},
        ],
        [
            {"ID": "QA-1", "状態": "回答済", "カテゴリ": "ops"},
            {"ID": "QA-2", "状態": "想定済", "カテゴリ": "ops"},
        ],
    )

    assert report["status"] == "pass"
    assert report["issue_blocker_count"] == 0
    assert report["qa_blocker_count"] == 0
