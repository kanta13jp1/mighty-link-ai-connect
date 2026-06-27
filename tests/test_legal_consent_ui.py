from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGAL_DOC_LINKS = [
    "docs/TERMS_OF_SERVICE.md",
    "docs/PRIVACY_POLICY.md",
    "docs/TOKUSHOHO_NOTATION.md",
    "docs/BILLING_AND_REFUND_POLICY.md",
]


def assert_legal_consent_ui(html: str):
    assert 'id="legal-consent-checkbox"' in html
    assert 'id="legal-consent-status"' in html
    assert 'const legalConsentVersion = "MSB-LEGAL-2026-06-DRAFT";' in html
    assert "legal_consent_accepted" in html
    assert "legal_consent_version" in html
    assert "getLegalConsentPayload()" in html
    assert "診断を実行するには、利用規約・プライバシーポリシー等への同意が必要です。" in html
    assert "<h3>法定・規約</h3>" in html
    for link in LEGAL_DOC_LINKS:
        assert html.count(link) >= 2


def test_public_index_has_legal_consent_ui_and_footer_links():
    html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_ui(html)


def test_src_index_has_legal_consent_ui_and_footer_links():
    html = (PROJECT_ROOT / "src" / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_ui(html)
