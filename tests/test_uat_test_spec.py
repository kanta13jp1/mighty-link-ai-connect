"""T882 test spec (written test-first): human-executable UAT test-specification guard.

The project has automated pytest suites but no *human-executable* test
specification (テスト仕様書) — a document a person can follow step by step and
mark OK/NG, which T845's manual production sign-off needs. This suite pins the
ten hypotheses the audit harness (scripts/audit_uat_test_spec.py) must verify so
the spec (docs/UAT_TEST_SPECIFICATION.md) stays complete, executable, and
consistent with the real WBS tasks and API endpoints:

* every case is uniquely IDed and carries all required fields (H2/H3),
* every case has >=2 numbered steps and explicit OK *and* NG criteria so a human
  can judge pass/fail unambiguously (H4/H5/H9),
* every referenced WBS id / API path really exists (H6/H7),
* all GA feature domains are covered (H8),
* the spec is drift-free overall (H1/H10).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_uat_test_spec as audit  # noqa: E402


# --------------------------------------------------------------------------- #
# Parser unit tests
# --------------------------------------------------------------------------- #
SAMPLE = """
# UAT
## 前書き `not_a_case`
### TS-01 適性アンケートの同意必須送信
- **対象機能**: 社内適性アンケート（同意ゲート）
- **関連WBS**: T840
- **関連API**: POST /api/employee-assessment/responses
- **前提条件**: 本番URLにアクセスでき社内確認コードを保有している
- **テスト手順**:
  1. アンケートセクションを開く
  2. 同意チェックを外したまま送信する
  3. 同意チェックを入れて送信する
- **期待結果**: 手順2は拒否、手順3は成功しresponse_idが返る
- **OK判定**: 手順2で送信不可、手順3で成功表示
- **NG判定**: 同意なしで送信できる、または同意ありで失敗
- **実施結果**: ☐ OK　☐ NG　／　実施日: ____　実施者: ____

### TS-02 公開デモのヘルスチェック
- **対象機能**: ヘルスチェック / 公開デモ
- **関連WBS**: T743
- **関連API**: GET /api/health
- **前提条件**: なし
- **テスト手順**:
  1. /api/health を開く
  2. status を確認する
- **期待結果**: HTTP 200 と status:ok が返る
- **OK判定**: 200 かつ status ok
- **NG判定**: 非200 または status not ok
- **実施結果**: ☐ OK　☐ NG
"""


def test_parse_extracts_only_ts_cases():
    cases = audit.parse_spec(SAMPLE)
    assert [c["id"] for c in cases] == ["TS-01", "TS-02"]
    assert "not_a_case" not in cases[0]["title"]


def test_parse_captures_fields_and_steps():
    case = audit.parse_spec(SAMPLE)[0]
    assert case["fields"]["関連WBS"] == "T840"
    assert case["fields"]["関連API"].startswith("POST /api/employee-assessment")
    assert len(case["steps"]) == 3
    assert case["fields"]["OK判定"] and case["fields"]["NG判定"]


def test_extract_api_path():
    assert audit.extract_api_path("POST /api/feedback") == "/api/feedback"
    assert audit.extract_api_path("GET /api/health 等") == "/api/health"
    assert audit.extract_api_path("なし (UI操作のみ)") is None


# --------------------------------------------------------------------------- #
# Evaluator unit tests (synthetic well-formed baseline + injected drift)
# --------------------------------------------------------------------------- #
def _case(cid, domain_kw, wbs="T840", api="POST /api/feedback", steps=3, ok="OK基準", ng="NG基準"):
    return {
        "id": cid,
        "title": f"{cid} {domain_kw}のテスト",
        "fields": {
            "対象機能": f"{domain_kw}機能",
            "関連WBS": wbs,
            "関連API": api,
            "前提条件": "前提",
            "テスト手順": "",
            "期待結果": "期待",
            "OK判定": ok,
            "NG判定": ng,
            "実施結果": "☐ OK　☐ NG",
        },
        "steps": [f"step{i}" for i in range(steps)],
    }


def _good_cases():
    # one case per required domain -> H8 satisfied, >=12 -> H1 satisfied
    return [
        _case(f"TS-{i+1:02d}", kw)
        for i, kw in enumerate(audit.REQUIRED_DOMAINS)
    ]


WBS_IDS = {"T840", "T841", "T817", "T842", "T745", "T781", "T742", "T790",
           "T763", "T877", "T743", "T753"}
API_PATHS = {"/api/feedback", "/api/health"}


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_evaluate_all_pass_on_good_spec():
    hyps = audit.evaluate(_good_cases(), WBS_IDS, API_PATHS)
    assert len(hyps) == 10
    failing = [h["id"] for h in hyps if not h["passed"]]
    assert failing == [], failing


def test_h1_flags_too_few_cases():
    hyps = _ids(audit.evaluate(_good_cases()[:5], WBS_IDS, API_PATHS))
    assert hyps["H1"]["passed"] is False


def test_h2_flags_duplicate_ids():
    cases = _good_cases()
    cases[1]["id"] = cases[0]["id"]
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H2"]["passed"] is False


def test_h3_flags_missing_required_field():
    cases = _good_cases()
    del cases[0]["fields"]["前提条件"]
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H3"]["passed"] is False


def test_h4_flags_too_few_steps():
    cases = _good_cases()
    cases[0]["steps"] = ["only one"]
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H4"]["passed"] is False


def test_h5_flags_missing_ok_or_ng_criteria():
    cases = _good_cases()
    cases[0]["fields"]["NG判定"] = ""
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H5"]["passed"] is False


def test_h6_flags_unknown_wbs():
    cases = _good_cases()
    cases[0]["fields"]["関連WBS"] = "T99999"
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_unknown_api_path():
    cases = _good_cases()
    cases[0]["fields"]["関連API"] = "POST /api/does-not-exist"
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H7"]["passed"] is False


def test_h8_flags_missing_domain_coverage():
    cases = _good_cases()[:-1]  # drop the last required domain
    # pad back to >=12 with a duplicate domain so only H8 (coverage) trips
    cases.append(_case("TS-99", audit.REQUIRED_DOMAINS[0]))
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H8"]["passed"] is False


def test_h9_flags_missing_ok_ng_marker():
    cases = _good_cases()
    cases[0]["fields"]["実施結果"] = "実施日: ____ のみ"
    hyps = _ids(audit.evaluate(cases, WBS_IDS, API_PATHS))
    assert hyps["H9"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: the real spec against the real repository
# --------------------------------------------------------------------------- #
def test_real_spec_is_complete_and_consistent():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing


def test_real_spec_covers_all_required_domains():
    report = audit.run_audit()
    assert report["missing_domains"] == [], report["missing_domains"]
    assert report["case_count"] >= 12
