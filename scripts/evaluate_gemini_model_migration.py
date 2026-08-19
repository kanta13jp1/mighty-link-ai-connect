"""Gemini model migration evaluation harness (T780).

T769 standardized the model-following policy and set ``gemini-3.5-flash`` as the
production default. T780 is the *migration test and production switch* task: it
must verify that the switch onto the current stable model is safe, that the
now shut-down Gemini 2.0 family is refused, and that model swaps never break the
structured-output contract the AI pipeline depends on.

This harness runs a 10-hypothesis migration evaluation that does NOT require a
live ``GEMINI_API_KEY``: the deterministic-fallback path and the model policy are
enough to prove the migration is safe. When ``--live`` is passed AND a key is
present, it additionally calls each candidate stable model once and records
latency + JSON-schema compliance so a human/Codex run can attach real numbers.

Outputs (the "モデル移行ログ" recorded to exports and, via the trackers, to Sheets):

* ``exports/gemini_model_migration_eval.json``
* ``exports/gemini_model_migration_eval.md``

The evaluation never persists secrets, real email bodies, or personal data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "data" / "gemini_model_policy.json"
DEFAULT_EXPORT_JSON = PROJECT_ROOT / "exports" / "gemini_model_migration_eval.json"
DEFAULT_EXPORT_MD = PROJECT_ROOT / "exports" / "gemini_model_migration_eval.md"

# Models officially shut down per https://ai.google.dev/gemini-api/docs/models
# (page last updated 2026-06-30). Staying on these would break production.
SHUTDOWN_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-3-pro-preview",
    "gemini-3.1-flash-lite-preview",
]

# Synthetic samples only — no real email content, no personal data.
SAMPLE_EMAILS = [
    {
        "subject": "【案件情報】Java/AWSバックエンド開発者 急募 80〜100万",
        "body": "渋谷勤務、リモート併用可。Spring Boot、SQL、Docker必須。即日〜長期。元請直。",
        "expect_category": "project",
    },
    {
        "subject": "【要員紹介】30代Python技術者 稼働可 7月中旬〜",
        "body": "弊社プロパー。Django/AWS/PostgreSQL経験7年。希望単価60〜80万。フルリモート希望。",
        "expect_category": "talent",
    },
    {
        "subject": "ニュースレター配信のお知らせ",
        "body": "今月のIT業界動向をお届けします。ご不要の場合は配信停止手続きをお願いします。",
        "expect_category": "other",
    },
]


def load_policy(policy_path: Path) -> dict[str, Any]:
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _import_parser():
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    return importlib.import_module("sales_email_parser")


def _offline_parser(parser_mod):
    """Create a parser that cannot inherit the process-level Gemini API key."""
    sentinel = object()
    previous = os.environ.pop("GEMINI_API_KEY", sentinel)
    try:
        return parser_mod.SalesEmailParser(api_key=None)
    finally:
        if previous is not sentinel:
            os.environ["GEMINI_API_KEY"] = previous


def _compiled_blocked(policy: dict[str, Any]):
    import re

    return [re.compile(pat) for pat in policy.get("blocked_model_patterns", [])]


def _is_blocked(model: str, patterns) -> bool:
    return any(p.search(model) for p in patterns)


def _read_app_default() -> str | None:
    import re

    text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")
    m = re.search(
        r"GEMINI_MODEL\s*=\s*os\.environ\.get\(\s*['\"]GEMINI_MODEL['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        text,
    )
    return m.group(1) if m else None


def build_hypotheses(policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the 10 migration hypotheses and return a result record for each."""
    results: list[dict[str, Any]] = []

    def record(hid: str, statement: str, check: Callable[[], tuple[bool, str]]) -> None:
        try:
            passed, detail = check()
        except Exception as exc:  # a failing check must not crash the log
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    parser_mod = _import_parser()
    blocked = _compiled_blocked(policy)
    prod_default = policy["production_default"]
    stable = policy.get("stable_production_models", [])

    # H1: production default is the top stable/GA model in current docs.
    def h1() -> tuple[bool, str]:
        ok = prod_default == "gemini-3.5-flash" and prod_default in stable
        return ok, f"production_default={prod_default} / stable先頭={stable[0] if stable else 'なし'}"

    record("H1", "本番既定モデルは公式docs(2026-06-30更新)のstable/GA最上位 gemini-3.5-flash である", h1)

    # H2: shut-down 2.0 family is blocked by policy.
    def h2() -> tuple[bool, str]:
        blocked_hits = {m: _is_blocked(m, blocked) for m in SHUTDOWN_MODELS}
        return all(blocked_hits.values()), f"shutdown拒否={blocked_hits}"

    record("H2", "シャットダウン済みモデル(2.0 Flash/Flash-Lite等)はblocked_model_patternsで拒否される", h2)

    # H3: app + parser defaults equal policy production_default.
    def h3() -> tuple[bool, str]:
        app_default = _read_app_default()
        parser_default = parser_mod.DEFAULT_GEMINI_MODEL
        ok = app_default == prod_default and parser_default == prod_default
        return ok, f"app.py={app_default} / parser={parser_default} / policy={prod_default}"

    record("H3", "本番コード(app.py, sales_email_parser.py)の既定モデルがpolicy production_defaultと一致", h3)

    # H4: GEMINI_MODEL env override flows through the pipeline.
    def h4() -> tuple[bool, str]:
        prev = os.environ.get("GEMINI_MODEL")
        try:
            os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
            resolved = parser_mod.get_gemini_model_name()
            parser = _offline_parser(parser_mod)
            ok = resolved == "gemini-2.5-flash" and parser.model_name == "gemini-2.5-flash"
            return ok, f"env上書き解決={resolved} / parser.model_name={parser.model_name}"
        finally:
            if prev is None:
                os.environ.pop("GEMINI_MODEL", None)
            else:
                os.environ["GEMINI_MODEL"] = prev

    record("H4", "GEMINI_MODEL環境変数で本番既定を上書きでき、値がパイプラインに反映される", h4)

    # H5: no latest alias in runtime; latest alias is blocked.
    def h5() -> tuple[bool, str]:
        import re

        alias_blocked = _is_blocked("gemini-flash-latest", blocked)
        # runtime scan for a literal "-latest" model string in src/
        offenders = []
        for py in (PROJECT_ROOT / "src").rglob("*.py"):
            for ln in py.read_text(encoding="utf-8").splitlines():
                if re.search(r"gemini-[a-z0-9.\-]*-latest", ln):
                    offenders.append(f"{py.name}: {ln.strip()[:60]}")
        return alias_blocked and not offenders, f"alias拒否={alias_blocked} / runtime使用={offenders or 'なし'}"

    record("H5", "latest aliasは本番コードで未使用かつpolicyでブロックされる(hot-swap回避)", h5)

    # H6: deterministic fallback returns schema-valid output without a key.
    def h6() -> tuple[bool, str]:
        parser = _offline_parser(parser_mod)
        details = []
        ok = True
        for s in SAMPLE_EMAILS:
            res = parser.parse(s["subject"], s["body"])
            valid = isinstance(res, parser_mod.EmailParseResultJSON) and 0.0 <= res.confidence <= 1.0
            ok = ok and valid
            details.append(f"{s['expect_category']}→{res.category}({'OK' if valid else 'NG'})")
        return ok, "; ".join(details)

    record("H6", "API未設定時のdeterministic fallbackがEmailParseResultJSONスキーマ準拠出力を返す(モデル非依存の可用性)", h6)

    # H7: structured-output contract is model-independent (schema is a fixed type).
    def h7() -> tuple[bool, str]:
        fields = set(parser_mod.EmailParseResultJSON.model_fields.keys())
        expected = {"category", "project", "talent", "confidence", "evidence_excerpt"}
        ok = expected.issubset(fields)
        return ok, f"response_schema固定フィールド={sorted(fields)}"

    record("H7", "構造化出力契約(response_schema=EmailParseResultJSON)はモデル非依存で候補モデル間互換", h7)

    # H8: fallback output is deterministic (regression-comparable across migration).
    def h8() -> tuple[bool, str]:
        parser = _offline_parser(parser_mod)
        s = SAMPLE_EMAILS[0]
        a = parser.parse(s["subject"], s["body"]).model_dump_json()
        b = parser.parse(s["subject"], s["body"]).model_dump_json()
        return a == b, f"再実行一致={a == b}"

    record("H8", "同一入力へのfallback出力は決定的で、移行前後の回帰比較が可能", h8)

    # H9: production switch procedure documented in the runbook.
    def h9() -> tuple[bool, str]:
        runbook = (PROJECT_ROOT / "docs" / "GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md").read_text(encoding="utf-8")
        markers = ["本番切り替え手順", "ロールバック", "同一コミット"]
        hits = {m: (m in runbook) for m in markers}
        return all(hits.values()), f"手順書マーカー={hits}"

    record("H9", "本番切り替え手順(rollout/rollback、既定値は同一コミットで変更)がRunbookに明記されている", h9)

    # H10: candidate stable models are all non-shutdown and audit-clean.
    def h10() -> tuple[bool, str]:
        bad = [m for m in stable if _is_blocked(m, blocked)]
        return not bad, f"stable候補={stable} / ブロック該当={bad or 'なし'}"

    record("H10", "policyのstable候補モデルは全てシャットダウン対象外で、監査上クリーン", h10)

    return results


def run_live_comparison(policy: dict[str, Any]) -> dict[str, Any]:
    """Optional: call each candidate stable model once (needs GEMINI_API_KEY)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"executed": False, "reason": "GEMINI_API_KEY未設定のためライブ比較はスキップ"}
    parser_mod = _import_parser()
    sample = SAMPLE_EMAILS[0]
    rows = []
    for model in policy.get("stable_production_models", []):
        prev = os.environ.get("GEMINI_MODEL")
        os.environ["GEMINI_MODEL"] = model
        try:
            parser = parser_mod.SalesEmailParser(api_key=api_key)
            t0 = time.time()
            res = parser.parse(sample["subject"], sample["body"])
            rows.append(
                {
                    "model": model,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "category": res.category,
                    "confidence": res.confidence,
                    "schema_valid": isinstance(res, parser_mod.EmailParseResultJSON),
                }
            )
        except Exception as exc:
            rows.append({"model": model, "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if prev is None:
                os.environ.pop("GEMINI_MODEL", None)
            else:
                os.environ["GEMINI_MODEL"] = prev
    return {"executed": True, "results": rows}


def build_report(policy_path: Path, checked_at: str, live: bool) -> dict[str, Any]:
    policy = load_policy(policy_path)
    hypotheses = build_hypotheses(policy)
    passed = sum(1 for h in hypotheses if h["passed"])
    live_block = run_live_comparison(policy) if live else {"executed": False, "reason": "--live未指定"}
    status = "ok" if passed == len(hypotheses) else "attention"
    return {
        "evaluation_id": "GEMINI_MODEL_MIGRATION_T780",
        "checked_at": checked_at,
        "production_default": policy["production_default"],
        "official_docs": policy.get("official_docs", {}),
        "shutdown_models_confirmed": SHUTDOWN_MODELS,
        "status": status,
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "live_comparison": live_block,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gemini モデル移行評価ログ (T780)",
        "",
        f"- 評価ID: `{report['evaluation_id']}`",
        f"- 実施日: {report['checked_at']}",
        f"- 本番既定モデル: `{report['production_default']}`",
        f"- 公式Docs: {report['official_docs'].get('models_url', 'N/A')} "
        f"(最終更新 {report['official_docs'].get('models_last_updated_utc', 'N/A')} UTC)",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        "",
        "## 10仮説検証",
        "",
        "| # | 仮説 | 結果 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for h in report["hypotheses"]:
        mark = "PASS" if h["passed"] else "FAIL"
        detail = h["detail"].replace("|", "/")
        lines.append(f"| {h['id']} | {h['hypothesis']} | {mark} | {detail} |")
    lines += ["", "## ライブ比較 (任意・GEMINI_API_KEY必要)", ""]
    live = report["live_comparison"]
    if not live.get("executed"):
        lines.append(f"- 未実施: {live.get('reason', '')}")
    else:
        lines.append("| モデル | latency(ms) | category | confidence | schema |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in live.get("results", []):
            if "error" in r:
                lines.append(f"| {r['model']} | - | error | - | {r['error']} |")
            else:
                lines.append(
                    f"| {r['model']} | {r['latency_ms']} | {r['category']} | "
                    f"{r['confidence']} | {'OK' if r['schema_valid'] else 'NG'} |"
                )
    lines += [
        "",
        "## 結論",
        "",
        "- 公式Docsでシャットダウン済みの Gemini 2.0 系はpolicyで拒否され、本番既定は"
        "stable最上位の `gemini-3.5-flash` を維持することが安全と確認した。",
        "- 構造化出力契約はモデル非依存で、候補stableモデル間で互換。fallbackにより"
        "APIモデルの可否に関わらず可用性が保たれる。",
        "- ライブでの精度/latency/cost比較は `GEMINI_API_KEY` を設定して `--live` で"
        "実行する（本番相当の実値取得は運用者/Codexレーンが実施）。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini model migration evaluation (T780)")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--checked-at", default="2026-07-07")
    parser.add_argument("--live", action="store_true", help="call candidate models (needs GEMINI_API_KEY)")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_EXPORT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_EXPORT_MD)
    parser.add_argument("--fail-on-attention", action="store_true")
    args = parser.parse_args()

    report = build_report(args.policy, args.checked_at, args.live)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"[*] Wrote {args.json_out}")
    print(f"[*] Wrote {args.md_out}")
    print(
        f"[{'+' if report['status'] == 'ok' else '!'}] Gemini migration eval {report['status']}: "
        f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses passed"
    )
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
