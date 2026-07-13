"""T876 frontend regression guard: session-only aptitude demo UI.

The backend T876_1 contract is already pinned by tests/test_aptitude_demo.py:
answers and derived scores are special-care personal information and must never
be persisted. This suite pins the frontend side of the same promise for both
HTML mirrors:

* the self-check section exists and is reachable from navigation,
* question/evaluation calls send the legal consent payload and explicit
  `consented: true`,
* the aptitude UI code does not use browser persistence APIs for answers.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]


def _aptitude_frontend_block(text: str) -> str:
    start = text.index("const aptitudeStaticQuestions")
    end = text.index("function setAttendanceStatus", start)
    return text[start:end]


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_aptitude_demo_section_and_navigation_exist(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    assert 'id="aptitude-demo-section"' in text
    assert 'href="#aptitude-demo-section"' in text
    assert 'id="aptitude-demo-consent"' in text
    assert 'id="aptitude-demo-questions"' in text
    assert 'id="aptitude-demo-result"' in text


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_aptitude_demo_calls_backend_with_legal_consent(path):
    block = _aptitude_frontend_block(path.read_text(encoding="utf-8", errors="replace"))
    assert '"/api/aptitude-demo/questions"' in block
    assert '"/api/aptitude-demo/evaluate"' in block
    assert "getLegalConsentPayload()" in block
    assert "legal_consent_accepted" in block
    assert "legal_consent_version" in block
    assert "legal_consent_accepted: legalConsent.legal_consent_accepted" in block
    assert "legal_consent_version: legalConsent.legal_consent_version" in block
    assert "consented: true" in block
    assert "body: JSON.stringify(requestPayload)" in block


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_aptitude_demo_frontend_does_not_persist_answers(path):
    block = _aptitude_frontend_block(path.read_text(encoding="utf-8", errors="replace"))
    lowered = block.lower()
    for forbidden in ("localstorage", "sessionstorage", "indexeddb", "document.cookie"):
        assert forbidden not in lowered, f"{path.name} aptitude UI must not use {forbidden}"
    assert "persisted: false" in block
    assert "保存なし" in block


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_aptitude_demo_has_static_demo_fallback_without_storage(path):
    block = _aptitude_frontend_block(path.read_text(encoding="utf-8", errors="replace"))
    assert "shouldUseAptitudeBrowserFallback" in block
    assert 'location.hostname.endsWith("github.io")' in block
    assert 'location.protocol === "file:"' in block
    assert "buildBrowserAptitudeQuestions" in block
    assert "evaluateAptitudeLocally" in block


def test_both_html_mirrors_have_same_aptitude_markers():
    blocks = [_aptitude_frontend_block(path.read_text(encoding="utf-8", errors="replace")) for path in HTML_FILES]
    markers = [
        "loadAptitudeQuestions",
        "evaluateAptitudeDemo",
        "collectAptitudeAnswers",
        "renderAptitudeResult",
        "aptitudePrivacyNotice",
    ]
    for marker in markers:
        assert all(marker in block for block in blocks), marker


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_aptitude_demo_analytics_tracks_section(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"const sectionIds = \[(.*?)\];", text, flags=re.S)
    assert m, path
    assert '"aptitude-demo-section"' in m.group(1)
