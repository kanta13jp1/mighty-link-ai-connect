from pathlib import Path


DESIGN = Path("docs/STRIPE_BILLING_INTEGRATION_DESIGN.md")
BILLING_POLICY = Path("docs/BILLING_AND_REFUND_POLICY.md")
PORTAL_RUNBOOK = Path("docs/STRIPE_CUSTOMER_PORTAL_RUNBOOK.md")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_t776_design_covers_billing_surfaces_and_follow_on_gates():
    content = read(DESIGN)
    required_terms = [
        "T776",
        "Checkout",
        "Subscription",
        "Billing Meters",
        "Webhook",
        "Customer Portal",
        "領収書",
        "請求書",
        "T791",
        "T807",
        "T813",
        "public_paid_launch",
        "No-Go",
    ]
    for term in required_terms:
        assert term in content


def test_t776_design_forbids_raw_payload_and_secret_sync():
    content = read(DESIGN)
    required_phrases = [
        "raw payloadはGitHub、Sheets、docs、NotebookLM、Slack、Issueへ保存しない",
        "Stripe signatureを検証",
        "冪等",
        "RLS",
        "REVOKE",
        "Webhook raw payload",
        "STRIPE_WEBHOOK_SECRET",
        "Customer Portal session URL",
        "カード番号",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_t776_design_defers_api_version_to_t791_recheck():
    content = read(DESIGN)
    assert "API versionは実装開始時点でStripe Dashboardと公式ドキュメントを再確認" in content
    assert "過去メモのAPI version文字列を根拠に実装しない" in content


def test_related_docs_point_to_t776_design():
    billing_policy = read(BILLING_POLICY)
    portal_runbook = read(PORTAL_RUNBOOK)
    assert "STRIPE_BILLING_INTEGRATION_DESIGN.md" in billing_policy
    assert "STRIPE_BILLING_INTEGRATION_DESIGN.md" in portal_runbook
