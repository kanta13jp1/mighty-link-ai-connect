"""T912 test spec (written test-first): architecture decision records (ADR).

UAT TS-42 (docs/UAT_TEST_SPECIFICATION.md): the project made several decisions
that a handover team (T850) cannot reconstruct from code — Firebase+Supabase
serverless, a dedicated mightylink-app.com on お名前.com instead of the company
domain, Gemini Flash as the model, Stripe for billing, the 3-lane AI workflow.
HOSTING_AND_DATABASE_SELECTION.md covered only hosting/DB and barely recorded
alternatives; the rest of the rationale was scattered.

This suite pins the ADR log's shape: numbered records with no duplicate/missing
ids, each carrying the six elements (context / decision / alternatives-with-
rejection-reason / consequences / status / evidence), the required decisions all
present, evidence links resolving to real files, and no credentials or company
registration facts embedded.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_architecture_decisions as guard  # noqa: E402

DOC = PROJECT_ROOT / "docs" / "ARCHITECTURE_DECISION_RECORDS.md"
DOCS_DIR = PROJECT_ROOT / "docs"

ELEMENTS = ["背景", "決定", "代替案", "影響", "ステータス", "根拠"]
REQUIRED_DECISIONS = ["ホスティング", "ドメイン", "AIモデル", "課金", "レーン"]
ALLOWED_STATUS = {"採用済み", "見直し中", "廃止"}

_ADR_RE = re.compile(r"^##\s+(ADR-(\d{4}))\s*[:：]?\s*(.*)$", re.M)


def read_doc() -> str:
    assert DOC.exists(), f"ADR log missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def _sections(text: str) -> dict[str, str]:
    """{ADR-NNNN: section text}."""
    out: dict[str, str] = {}
    matches = list(_ADR_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def test_adr_ids_are_sequential_and_unique():
    ids = [int(m.group(2)) for m in _ADR_RE.finditer(read_doc())]
    assert ids, "no ADR sections found"
    assert len(ids) == len(set(ids)), f"duplicate ADR ids: {ids}"
    assert ids == list(range(1, len(ids) + 1)), f"ADR ids must be 1..N with no gaps: {ids}"


def test_every_adr_has_the_six_elements():
    missing: dict[str, list[str]] = {}
    for adr, body in _sections(read_doc()).items():
        gaps = [e for e in ELEMENTS if e not in body]
        if gaps:
            missing[adr] = gaps
    assert not missing, f"ADRs missing required elements: {missing}"


def test_alternatives_are_not_empty():
    """A decision without a rejected alternative is not a decision record."""
    thin: list[str] = []
    for adr, body in _sections(read_doc()).items():
        m = re.search(r"代替案[^\n]*\n(.*?)(?=\n- \*\*|\n## |\Z)", body, re.S)
        if not m or len(m.group(1).strip()) < 20:
            thin.append(adr)
    assert not thin, f"ADRs with empty/too-thin alternatives: {thin}"


def test_required_decisions_are_covered():
    text = read_doc()
    missing = [d for d in REQUIRED_DECISIONS if d not in text]
    assert not missing, f"required decisions not recorded: {missing}"


def test_status_values_are_allowed():
    bad: dict[str, str] = {}
    for adr, body in _sections(read_doc()).items():
        m = re.search(r"ステータス\*\*\s*[:：]?\s*([^\n|]+)", body)
        if m:
            value = m.group(1).strip().strip("*").strip()
            if not any(s in value for s in ALLOWED_STATUS):
                bad[adr] = value
    assert not bad, f"ADRs with disallowed status: {bad}"


def test_evidence_links_resolve():
    """Every docs/*.md link in the ADR log must exist."""
    dangling: list[str] = []
    for m in re.finditer(r"\]\(([A-Za-z0-9_./-]+\.md)\)", read_doc()):
        target = (DOCS_DIR / m.group(1)).resolve()
        if not target.exists():
            dangling.append(m.group(1))
    assert not dangling, f"dangling evidence links: {sorted(set(dangling))}"


def test_no_credentials_or_registration_facts():
    text = read_doc()
    for pattern in (r"sk_(?:live|test)_", r"AIza[0-9A-Za-z_-]{10,}", r"〒\d{3}-\d{4}"):
        assert not re.search(pattern, text), f"forbidden content matched: {pattern}"


def test_guard_pure_functions_agree_with_the_document():
    """Exercise the guard module itself (gives it a CI path per preflight H7)."""
    text = read_doc()
    assert guard.adr_ids(text) == list(range(1, len(guard.adr_sections(text)) + 1))
    assert guard.missing_required(text) == []
    assert guard.dangling_links(text) == []
    for adr, body in guard.adr_sections(text).items():
        assert guard.missing_elements(body) == [], f"{adr} missing elements"
        assert len(guard.alternatives_text(body)) >= 20, f"{adr} alternatives too thin"


def test_guard_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"ADR hypotheses failing on real repo: {failed}"
