"""T862_1 test spec (written test-first): paid-launch decision pack guard.

UAT TS-29 (docs/UAT_TEST_SPECIFICATION.md): the paid-launch Go/No-Go decision
(T862, first monthly review 2026-07-24) needs a decision pack a human can read
to choose Go / No-Go / 保留. This suite pins the machine-checkable half: the
pack exists, states its decision date and that it is a management decision,
carries the seven decision materials tied to source docs, frames Go/No-Go/保留
neutrally, lays out the Go-path implementation order (T791→T807→T813→T793),
gives withdrawal/hold conditions, includes the T900 legal-disclosure readiness,
and carries no credential-shaped strings.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC = PROJECT_ROOT / "docs" / "PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md"

# The seven decision materials T862 requires.
MATERIALS = ["社内利用実績", "コスト", "SLA", "解約", "インボイス", "サポート", "法定開示"]

# Go-path implementation tasks in order.
GO_PATH = ["T791", "T807", "T813", "T793"]

FORBIDDEN_PATTERNS = [
    re.compile(r"sk_(?:live|test)_", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"Bearer\s+[0-9A-Za-z._-]{16,}"),
    re.compile(r"パスワード\s*[:：]\s*\S"),
]


def read_doc() -> str:
    assert DOC.exists(), f"paid-launch decision pack missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def test_states_date_and_management_decision():
    text = read_doc()
    assert "2026-07-24" in text
    assert "T862" in text and "T862_1" in text
    assert "経営判断" in text


def test_covers_seven_decision_materials():
    text = read_doc()
    for material in MATERIALS:
        assert material in text, f"decision material missing: {material}"


def test_frames_go_nogo_hold_neutrally():
    text = read_doc()
    assert "Go" in text
    assert "No-Go" in text or "No Go" in text
    assert "保留" in text


def test_lays_out_go_path_in_order():
    text = read_doc()
    positions = [text.find(t) for t in GO_PATH]
    assert all(p >= 0 for p in positions), f"Go-path task missing: {GO_PATH}"
    assert positions == sorted(positions), "Go-path tasks are not in T791→T807→T813→T793 order"


def test_has_withdrawal_or_hold_conditions():
    text = read_doc()
    assert "撤退" in text or "保留条件" in text or "持ち越し" in text


def test_includes_legal_disclosure_readiness():
    text = read_doc()
    assert "T900" in text
    assert "要法務確認" in text or "未確定" in text


def test_no_credential_shaped_strings():
    text = read_doc()
    for pattern in FORBIDDEN_PATTERNS:
        assert not pattern.search(text), f"credential-shaped match: {pattern.pattern}"
