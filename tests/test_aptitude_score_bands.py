"""T909 test spec (written test-first): score bands + feedback-interview guide.

2026-07-22 社長定例決定事項(1): a bare score ("54.3点") tells an employee
nothing — the result must state what counts as 正常 / 注意 / 面談目安, and give a
manager material for the monthly 10-20 minute feedback conversation.

Pinned here:

* The band thresholds are ONE source of truth (aptitude_demo.SCORE_BANDS) that
  the evaluator, the API legend and the UI all read, so the legend can never
  disagree with the判定 an employee is shown.
* Bands tile the 0-100 range with no gap and no overlap.
* The interview guide is generic self-care wording keyed off the band and the
  weakest dimension — never a diagnosis, never a directive about treatment.
* R119 / QA-105 still holds: nothing here persists, and the guide must not
  leak the score into anything stored.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import aptitude_demo  # noqa: E402
import app as app_module  # noqa: E402

client = TestClient(app_module.app)
LEGAL_VERSION = app_module.LEGAL_CONSENT_VERSION


# --------------------------------------------------------------------------- #
# SCORE_BANDS: the single source of truth
# --------------------------------------------------------------------------- #
def test_bands_are_three_ordered_levels():
    bands = aptitude_demo.SCORE_BANDS
    assert [b["id"] for b in bands] == ["watch", "moderate", "good"]
    for band in bands:
        assert {"id", "label", "min_index", "max_index", "guidance", "follow_up"} <= set(band)


def test_bands_are_labelled_for_the_ceo_request():
    labels = {b["id"]: b["label"] for b in aptitude_demo.SCORE_BANDS}
    assert labels["good"] == "正常"
    assert labels["moderate"] == "注意"
    assert labels["watch"] == "面談目安"


def test_bands_tile_the_full_range_without_gap_or_overlap():
    bands = sorted(aptitude_demo.SCORE_BANDS, key=lambda b: b["min_index"])
    assert bands[0]["min_index"] == 0
    assert bands[-1]["max_index"] == 100
    for lower, upper in zip(bands, bands[1:]):
        assert upper["min_index"] > lower["max_index"], "bands overlap"
        # contiguous to one decimal place (scores are rounded to 0.1)
        assert round(upper["min_index"] - lower["max_index"], 2) == 0.1, "gap between bands"


def test_band_for_index_matches_the_table():
    for band in aptitude_demo.SCORE_BANDS:
        assert aptitude_demo.band_for_index(band["min_index"])["id"] == band["id"]
        assert aptitude_demo.band_for_index(band["max_index"])["id"] == band["id"]


def test_band_boundaries_are_the_documented_thresholds():
    assert aptitude_demo.band_for_index(75.0)["id"] == "good"
    assert aptitude_demo.band_for_index(74.9)["id"] == "moderate"
    assert aptitude_demo.band_for_index(50.0)["id"] == "moderate"
    assert aptitude_demo.band_for_index(49.9)["id"] == "watch"
    # the CEO's example score sits in 注意
    assert aptitude_demo.band_for_index(54.3)["id"] == "moderate"


def test_index_out_of_range_is_clamped_not_crashed():
    assert aptitude_demo.band_for_index(-5)["id"] == "watch"
    assert aptitude_demo.band_for_index(150)["id"] == "good"


# --------------------------------------------------------------------------- #
# evaluate_responses reads the same table
# --------------------------------------------------------------------------- #
def _answers(value, n=10):
    return [{"dimension": "energy", "value": value} for _ in range(n)]


def test_evaluate_band_agrees_with_band_for_index():
    for value in (1, 2, 3, 4, 5):
        result = aptitude_demo.evaluate_responses(_answers(value))
        assert result["band"] == aptitude_demo.band_for_index(result["condition_index"])["id"]


def test_evaluate_exposes_the_band_label_and_thresholds():
    result = aptitude_demo.evaluate_responses(_answers(3))
    assert result["band_label"] == "注意"
    assert result["band_range"] == [50.0, 74.9]
    assert result["score_bands"] == aptitude_demo.SCORE_BANDS


# --------------------------------------------------------------------------- #
# feedback interview guide
# --------------------------------------------------------------------------- #
def test_interview_guide_returns_talking_points_and_focus():
    result = aptitude_demo.evaluate_responses(
        [{"dimension": "energy", "value": 2}, {"dimension": "focus", "value": 5}]
    )
    guide = result["interview_guide"]
    assert guide["focus_dimension"] == "energy", "the weakest dimension leads the conversation"
    assert len(guide["talking_points"]) >= 3
    assert guide["suggested_minutes"] == "10〜20分"


def test_interview_guide_is_not_medical_or_directive():
    forbidden = ("診断", "病名", "薬", "治療", "うつ", "休職を命")
    for value in (1, 3, 5):
        guide = aptitude_demo.evaluate_responses(_answers(value))["interview_guide"]
        blob = " ".join(guide["talking_points"]) + guide["opening"] + guide["caution"]
        for term in forbidden:
            assert term not in blob, f"interview guide must avoid {term}"


def test_interview_guide_warns_it_is_not_an_evaluation():
    guide = aptitude_demo.evaluate_responses(_answers(2))["interview_guide"]
    assert "人事評価" in guide["caution"], "must state it is not a personnel evaluation"


# --------------------------------------------------------------------------- #
# API surface
# --------------------------------------------------------------------------- #
def test_legend_endpoint_serves_the_bands():
    res = client.get("/api/aptitude-demo/legend")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["score_bands"] == aptitude_demo.SCORE_BANDS
    assert body["scale"]["min"] == 1 and body["scale"]["max"] == 5


def test_evaluate_endpoint_returns_band_label_and_guide():
    res = client.post("/api/aptitude-demo/evaluate", json={
        "answers": [{"dimension": "energy", "value": 2}],
        "consented": True,
        "legal_consent_accepted": True,
        "legal_consent_version": LEGAL_VERSION,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["band_label"] in {"正常", "注意", "面談目安"}
    assert body["interview_guide"]["talking_points"]
    assert body["persisted"] is False


# --------------------------------------------------------------------------- #
# R119: still no persistence anywhere in this module
# --------------------------------------------------------------------------- #
def test_module_still_imports_no_storage():
    source = (PROJECT_ROOT / "src" / "aptitude_demo.py").read_text(encoding="utf-8")
    for forbidden in ("sqlite3", "supabase", "psycopg", "get_db_connection", "INSERT INTO"):
        assert forbidden not in source, f"aptitude_demo must stay storage-free ({forbidden})"


# --------------------------------------------------------------------------- #
# UI: legend + interview panel + standalone route, mirrored
# --------------------------------------------------------------------------- #
def assert_band_ui(html: str):
    assert 'id="aptitude-band-legend"' in html
    assert "function renderAptitudeBandLegend(" in html
    assert "/api/aptitude-demo/legend" in html
    assert 'id="aptitude-interview-guide"' in html
    assert "function renderAptitudeInterviewGuide(" in html
    # standalone demo route for sharing the self-check on its own
    assert "#aptitude-demo-standalone" in html
    assert "function applyAptitudeStandaloneRoute()" in html
    # the three labels must be visible to the employee
    for label in ("正常", "注意", "面談目安"):
        assert label in html


def test_public_index_has_band_ui():
    assert_band_ui((PROJECT_ROOT / "index.html").read_text(encoding="utf-8"))


def test_src_index_has_band_ui():
    assert_band_ui((PROJECT_ROOT / "src" / "index.html").read_text(encoding="utf-8"))


def test_static_fallback_bands_match_the_server():
    """The GitHub Pages build evaluates locally; its bands must not drift."""
    html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    start = html.index("const aptitudeScoreBands = [")
    block = html[start: html.index("];", start)]
    for band in aptitude_demo.SCORE_BANDS:
        assert f'id: "{band["id"]}"' in block
        assert f'label: "{band["label"]}"' in block
        assert f'min_index: {band["min_index"]}' in block
