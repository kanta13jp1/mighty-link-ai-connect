"""T752 test spec (written test-first): onboarding / activation flow.

PUBLIC-06 (BLOCKED on T752) requires "ユーザーオンボーディング/アカウント登録/
アクティベーションフローが実装済み", with docs/USER_GUIDE_AND_FAQ.md, index.html
and src/app.py as its evidence sources.

Internal GA issues accounts administratively (T833), so activation — not
self-signup — is the flow that matters: an issued account completes a guided
setup wizard and is then activated, gated on the current legal consent version.

Design pinned here:
* the step catalogue is SERVER-canonical (GET /api/onboarding/state) so the
  wizard UI and the activation validator cannot drift apart;
* activation refuses missing required steps and stale/absent legal consent;
* the account identifier is pseudonymized — no raw identifier is returned or
  audited (same privacy stance as the attendance/aptitude features, and it
  keeps T752 clear of the still-open T798 legal review by storing no PII row).
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import app as app_module  # noqa: E402

client = TestClient(app_module.app)

LEGAL_VERSION = app_module.LEGAL_CONSENT_VERSION


def _required_ids() -> list[str]:
    state = client.get("/api/onboarding/state").json()
    return [s["id"] for s in state["steps"] if s["required"]]


def _activate_payload(**overrides):
    payload = {
        "account_identifier": "onboarding-tester",
        "completed_step_ids": _required_ids(),
        "legal_consent_accepted": True,
        "legal_consent_version": LEGAL_VERSION,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# GET /api/onboarding/state — the server-canonical wizard definition
# --------------------------------------------------------------------------- #
def test_state_exposes_ordered_step_catalogue():
    res = client.get("/api/onboarding/state")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["flow_version"] == app_module.ONBOARDING_FLOW_VERSION
    assert body["legal_consent_version"] == LEGAL_VERSION
    steps = body["steps"]
    assert len(steps) >= 4
    for step in steps:
        assert {"id", "title", "description", "required"} <= set(step)
    # order is stable and ids unique
    ids = [s["id"] for s in steps]
    assert len(ids) == len(set(ids))
    assert ids == [s["id"] for s in app_module.ONBOARDING_STEPS]


def test_state_requires_account_and_legal_consent_steps():
    required = _required_ids()
    assert "account" in required
    assert "legal_consent" in required


# --------------------------------------------------------------------------- #
# POST /api/onboarding/progress — progress computed against the canonical steps
# --------------------------------------------------------------------------- #
def test_progress_reports_remaining_required_steps():
    res = client.post("/api/onboarding/progress", json={"completed_step_ids": ["account"]})
    assert res.status_code == 200
    body = res.json()
    assert "account" in body["completed_step_ids"]
    assert "legal_consent" in body["remaining_required_step_ids"]
    assert body["can_activate"] is False
    assert 0 < body["progress_pct"] < 100


def test_progress_can_activate_when_all_required_done():
    res = client.post("/api/onboarding/progress", json={"completed_step_ids": _required_ids()})
    body = res.json()
    assert body["remaining_required_step_ids"] == []
    assert body["can_activate"] is True


def test_progress_ignores_unknown_step_ids():
    res = client.post(
        "/api/onboarding/progress",
        json={"completed_step_ids": ["account", "not-a-real-step"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert "not-a-real-step" not in body["completed_step_ids"]
    assert "not-a-real-step" in body["ignored_step_ids"]


# --------------------------------------------------------------------------- #
# POST /api/onboarding/activate — the gate
# --------------------------------------------------------------------------- #
def test_activate_succeeds_and_pseudonymizes_the_identifier():
    raw = "onboarding-tester"
    res = client.post("/api/onboarding/activate", json=_activate_payload(account_identifier=raw))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "success"
    assert body["activated"] is True
    assert body["auth_status"] == "authenticated"
    assert body["session_token"].startswith("sess_onb_")
    assert body["subject_pseudonym"].startswith("onb-")
    assert body["flow_version"] == app_module.ONBOARDING_FLOW_VERSION
    assert body["legal_consent_version"] == LEGAL_VERSION
    assert body["activated_at"]
    assert body["audit_event_id"]
    # the raw identifier must never be echoed back
    assert raw not in res.text


def test_activate_is_deterministic_per_identifier():
    a = client.post("/api/onboarding/activate", json=_activate_payload()).json()
    b = client.post("/api/onboarding/activate", json=_activate_payload()).json()
    assert a["subject_pseudonym"] == b["subject_pseudonym"]


def test_activate_rejects_missing_required_steps():
    res = client.post("/api/onboarding/activate", json=_activate_payload(completed_step_ids=["account"]))
    assert res.status_code == 400
    assert "legal_consent" in res.json()["detail"]


def test_activate_rejects_unaccepted_legal_consent():
    res = client.post("/api/onboarding/activate", json=_activate_payload(legal_consent_accepted=False))
    assert res.status_code == 400
    assert "legal consent" in res.json()["detail"].lower()


def test_activate_rejects_stale_legal_consent_version():
    res = client.post(
        "/api/onboarding/activate",
        json=_activate_payload(legal_consent_version="MSB-LEGAL-2000-01-OLD"),
    )
    assert res.status_code == 400
    assert "version" in res.json()["detail"].lower()


def test_activate_rejects_blank_account_identifier():
    res = client.post("/api/onboarding/activate", json=_activate_payload(account_identifier="  "))
    assert res.status_code == 400
    assert "account_identifier" in res.json()["detail"]


# --------------------------------------------------------------------------- #
# UI: the wizard exists in BOTH index mirrors and is driven by the server steps
# --------------------------------------------------------------------------- #
def assert_onboarding_ui(html: str):
    assert 'id="onboarding-section"' in html
    assert 'href="#onboarding-section"' in html, "nav link to the wizard"
    assert 'id="onboarding-steps"' in html
    assert 'id="onboarding-progress"' in html
    assert 'id="onboarding-status"' in html
    assert 'id="onboarding-account-identifier"' in html
    assert 'id="onboarding-activate"' in html
    # server-canonical: the wizard loads its steps from the API, never hardcodes them
    assert "/api/onboarding/state" in html
    assert "/api/onboarding/activate" in html
    assert "function loadOnboardingState()" in html
    assert "function activateOnboarding()" in html
    assert "function renderOnboardingSteps(" in html
    # progress persists locally between visits (no PII row server-side)
    assert "msb_onboarding_progress_v1" in html


def test_public_index_has_onboarding_ui():
    assert_onboarding_ui((PROJECT_ROOT / "index.html").read_text(encoding="utf-8"))


def test_src_index_has_onboarding_ui():
    assert_onboarding_ui((PROJECT_ROOT / "src" / "index.html").read_text(encoding="utf-8"))


def test_index_mirrors_stay_identical():
    assert (PROJECT_ROOT / "index.html").read_text(encoding="utf-8") == (
        PROJECT_ROOT / "src" / "index.html"
    ).read_text(encoding="utf-8")


def test_static_fallback_steps_match_the_server_catalogue():
    """The GitHub Pages build has no API, so the wizard carries a copy of the
    catalogue. That copy must not drift from src/app.py's ONBOARDING_STEPS —
    otherwise the public demo would teach a different flow than the one the
    activation gate enforces.
    """
    html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    start = html.index("const onboardingStaticSteps = [")
    end = html.index("];", start)
    block = html[start:end]
    for step in app_module.ONBOARDING_STEPS:
        assert f'id: "{step["id"]}"' in block, f"static fallback missing step {step['id']}"
        assert f'title: "{step["title"]}"' in block, f"title drift on {step['id']}"
        assert f'description: "{step["description"]}"' in block, f"description drift on {step['id']}"
        assert f'required: {"true" if step["required"] else "false"}' in block.split(
            f'id: "{step["id"]}"'
        )[1].split("}")[0], f"required flag drift on {step['id']}"
    # no extra steps invented client-side
    assert block.count('id: "') == len(app_module.ONBOARDING_STEPS)


def test_user_guide_documents_the_onboarding_flow():
    guide = (PROJECT_ROOT / "docs" / "USER_GUIDE_AND_FAQ.md").read_text(encoding="utf-8")
    assert "オンボーディング" in guide
    assert "アクティベーション" in guide
    for step in app_module.ONBOARDING_STEPS:
        if step["required"]:
            assert step["title"] in guide, f"required step undocumented: {step['id']}"
