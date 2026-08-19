import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import evaluate_gemini_model_migration as evalmod


def test_migration_eval_all_hypotheses_pass_on_real_repo():
    report = evalmod.build_report(evalmod.DEFAULT_POLICY_PATH, "2026-07-07", live=False)
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["hypotheses_total"] == 10
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["status"] == "ok"


def test_production_default_is_current_stable_top():
    report = evalmod.build_report(evalmod.DEFAULT_POLICY_PATH, "2026-07-07", live=False)
    assert report["production_default"] == "gemini-3.5-flash"


def test_shutdown_models_are_blocked():
    policy = evalmod.load_policy(evalmod.DEFAULT_POLICY_PATH)
    patterns = evalmod._compiled_blocked(policy)
    for model in evalmod.SHUTDOWN_MODELS:
        assert evalmod._is_blocked(model, patterns), f"{model} should be blocked"


def test_live_comparison_skipped_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    policy = evalmod.load_policy(evalmod.DEFAULT_POLICY_PATH)
    result = evalmod.run_live_comparison(policy)
    assert result["executed"] is False


def test_offline_parser_ignores_process_api_key_and_restores_it(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-placeholder-key")
    parser_mod = evalmod._import_parser()

    parser = evalmod._offline_parser(parser_mod)

    assert parser.client is None
    assert parser.api_key is None
    assert evalmod.os.environ["GEMINI_API_KEY"] == "test-placeholder-key"


def test_report_json_is_serializable(tmp_path):
    report = evalmod.build_report(evalmod.DEFAULT_POLICY_PATH, "2026-07-07", live=False)
    out = tmp_path / "eval.json"
    out.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    assert json.loads(out.read_text(encoding="utf-8"))["evaluation_id"] == "GEMINI_MODEL_MIGRATION_T780"
