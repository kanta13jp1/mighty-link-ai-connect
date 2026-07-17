"""Lane preflight guard (T894).

The 16 domain guards (scripts/audit_*.py) each protect their own slice, and each
is exercised by CI. What was missing is the step that runs them *before a lane
commits*: AGENTS.md's Required Session Closeout listed only the generate/sync
scripts, so a lane could follow the documented process exactly and still push a
red tree. On 2026-07-16 that happened (R123): another lane's uncommitted edit had
deleted UAT cases TS-11/TS-12, leaving pytest at 3 failed / 455 passed.

This harness is the single command a lane runs first:

    python scripts/run_lane_preflight.py          # fast: 16 guards only
    python scripts/run_lane_preflight.py --full   # + the whole pytest suite

Ten hypotheses keep the aggregation itself honest: no guard may be added without
being registered, no registered guard may be stale, lack a CI path (no test
imports it) or skip its evidence, the suite may not silently shrink, and
AGENTS.md must keep documenting the command.

Guards own their own verdicts; this runner only aggregates them (no duplicated
judgement logic). Output: exports/lane_preflight_report.{json,md}. No secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"
EXPORTS_DIR = PROJECT_ROOT / "exports"
AGENTS_MD = PROJECT_ROOT / "AGENTS.md"
DEFAULT_JSON = EXPORTS_DIR / "lane_preflight_report.json"
DEFAULT_MD = EXPORTS_DIR / "lane_preflight_report.md"

PREFLIGHT_COMMAND = "run_lane_preflight.py"

MIN_GUARDS = 10
MIN_TEST_FILES = 50
MIN_COLLECTED_TESTS = 400

# Every scripts/audit_*.py is partitioned into GUARD_REGISTRY (repo-integrity
# guards run by the preflight) or EXEMPT_GUARDS (reason noted). H2/H3 keep the
# partition exhaustive, so a new guard cannot ship without a decision.
GUARD_REGISTRY: dict[str, str] = {
    "audit_access_inventory.py": "権限棚卸し・Break-glass・単一障害点 (T850_1)",
    "audit_admin_dashboard_error_handling.py": "管理者ダッシュボードのエラー処理",
    "audit_diagnosis_fallback_transparency.py": "診断fallbackの利用者への透明性",
    "audit_docs_reference_integrity.py": "docs内リンクの実在・移植性 (T891)",
    "audit_fk_index_coverage.py": "外部キーのインデックス網羅",
    "audit_form_error_handling.py": "フォーム入力エラー処理",
    "audit_frontend_api_contract.py": "フロントエンドとAPI契約の整合",
    "audit_gemini_model_policy.py": "Geminiモデル版ポリシー適合",
    "audit_issue_qa_blockers.py": "課題/QAの開発ブロッカーゼロ (T854)",
    "audit_sales_email_hardening.py": "営業メール処理の堅牢化",
    "audit_schema_doc_consistency.py": "DBスキーマとdocsの整合",
    "audit_tracker_integrity.py": "課題管理表/QA表の構造・参照整合 (T890)",
    "audit_uat_api_coverage.py": "UAT⇄API網羅トレーサビリティ (T892)",
    "audit_uat_test_spec.py": "UAT仕様書の完全性・実行可能性 (T882)",
    "audit_wbs_lifecycle_coverage.py": "WBSライフサイクル7工程の網羅 (T889)",
}

# Guards that are NOT repo-integrity checks and must not gate a commit.
EXEMPT_GUARDS: dict[str, str] = {
    "audit_external_api_usage.py":
        "運用日次ツール(T736): 正本がgitignoreのローカル台帳 data/external_api_usage.jsonl で、"
        "レポート先も reports/。作業ツリーの整合とは無関係なためプリフライト対象外",
}


def utf8_subprocess_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment that keeps Python guard output UTF-8 on Windows."""
    env = dict(os.environ if base is None else base)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def configure_utf8_console() -> None:
    """Allow Japanese reports and verdict symbols on CP932 consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def discover_guards(scripts_dir: Path = SCRIPTS_DIR) -> set[str]:
    """Return the audit guard filenames present on disk."""
    return {p.name for p in scripts_dir.glob("audit_*.py")}


def find_imported_guards(tests_dir: Path = TESTS_DIR) -> set[str]:
    """Return guards imported by at least one test (i.e. reached by CI).

    Detected by import statement rather than by test filename, because the repo
    uses both test_<guard>.py and test_<guard>_audit.py naming.
    """
    imported: set[str] = set()
    for test_file in tests_dir.glob("test_*.py"):
        text = test_file.read_text(encoding="utf-8", errors="replace")
        for module in re.findall(r"^\s*(?:import|from)\s+(audit_[A-Za-z0-9_]+)", text, re.M):
            imported.add(f"{module}.py")
    return imported


def count_test_files(tests_dir: Path = TESTS_DIR) -> int:
    return len(list(tests_dir.glob("test_*.py")))


def closeout_documents_preflight(agents_md: Path = AGENTS_MD) -> bool:
    """H9: AGENTS.md's closeout must still name this command."""
    if not agents_md.exists():
        return False
    return PREFLIGHT_COMMAND in agents_md.read_text(encoding="utf-8", errors="replace")


def declared_evidence(guard: str, scripts_dir: Path = SCRIPTS_DIR) -> str | None:
    """Return the exports/*.md artefact the guard declares in its own source.

    Read from the guard rather than guessed from its filename: the artefact names
    do not track the script names (audit_issue_qa_blockers.py writes
    issue_qa_blocker_audit.md), so guessing produces false positives.
    """
    path = scripts_dir / guard
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"exports"\s*/\s*"([^"]+\.md)"', text)
    return m.group(1) if m else None


def _evidence_exists(guard: str, exports_dir: Path = EXPORTS_DIR) -> bool:
    """True when the guard's declared markdown artefact exists under exports/."""
    name = declared_evidence(guard)
    return bool(name) and (exports_dir / name).exists()


def run_guards(registry: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """Execute each registered guard and collect its exit code + evidence."""
    registry = registry if registry is not None else GUARD_REGISTRY
    results: dict[str, dict[str, Any]] = {}
    for guard in sorted(registry):
        path = SCRIPTS_DIR / guard
        if not path.exists():
            results[guard] = {"exit_code": 127, "evidence": False}
            continue
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=utf8_subprocess_env(),
        )
        results[guard] = {
            "exit_code": proc.returncode,
            "evidence": _evidence_exists(guard),
        }
        mark = "OK " if proc.returncode == 0 else "FAIL"
        print(f"  [{mark}] {guard}")
    return results


def run_pytest() -> dict[str, Any]:
    """Run the full suite and parse the summary line."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_subprocess_env(),
    )
    out = proc.stdout + proc.stderr
    failed = sum(int(n) for n in re.findall(r"(\d+) failed", out))
    errors = sum(int(n) for n in re.findall(r"(\d+) errors?", out))
    passed = sum(int(n) for n in re.findall(r"(\d+) passed", out))
    return {
        "skipped": False,
        "failed": failed,
        "errors": errors,
        "collected": passed + failed + errors,
        "exit_code": proc.returncode,
    }


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(
    discovered: set[str],
    registry: dict[str, str],
    guard_results: dict[str, dict[str, Any]],
    pytest_result: dict[str, Any],
    imported_guards: set[str],
    test_file_count: int,
    closeout_has_preflight: bool,
    exempt: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    registered = set(registry)
    exempted = set(exempt or {})
    classified = registered | exempted

    results.append(_hyp("H1", f"プリフライト対象ガード{MIN_GUARDS}件以上かつテストファイル{MIN_TEST_FILES}件以上(sanity)",
                        len(registered) >= MIN_GUARDS and test_file_count >= MIN_TEST_FILES,
                        f"対象ガード={len(registered)}, 対象外={len(exempted)}, テストファイル={test_file_count}"))

    unclassified = sorted(discovered - classified)
    results.append(_hyp("H2", "全scripts/audit_*.pyがGUARD_REGISTRY∪EXEMPT_GUARDSに分類済み(未分類0)",
                        not unclassified, f"未分類={unclassified or 'なし'}"))

    stale = sorted(classified - discovered)
    results.append(_hyp("H3", "分類済みガードが全て実在(stale分類0)",
                        not stale, f"stale={stale or 'なし'}"))

    failing = sorted(g for g, r in guard_results.items() if r.get("exit_code") != 0)
    results.append(_hyp("H4", "登録ガードの実行終了コードが全て0(全ガードPASS)",
                        not failing, f"FAIL={failing or 'なし'}"))

    if pytest_result.get("skipped"):
        results.append(_hyp("H5", "pytest tests/ の failed/error が0",
                            True, "高速モード(未実行) — push前に --full を実行すること"))
        results.append(_hyp("H6", f"収集テストが{MIN_COLLECTED_TESTS}件以上(スイート縮退検知)",
                            True, "高速モード(未実行) — push前に --full を実行すること"))
    else:
        failed = int(pytest_result.get("failed", 0))
        errors = int(pytest_result.get("errors", 0))
        results.append(_hyp("H5", "pytest tests/ の failed/error が0",
                            failed == 0 and errors == 0,
                            f"failed={failed}, errors={errors}"))
        collected = int(pytest_result.get("collected", 0))
        results.append(_hyp("H6", f"収集テストが{MIN_COLLECTED_TESTS}件以上(スイート縮退検知)",
                            collected >= MIN_COLLECTED_TESTS, f"収集={collected}"))

    no_ci_path = sorted(registered - set(imported_guards))
    results.append(_hyp("H7", "全対象ガードがtests/のいずれかからimportされている(CI実行経路あり)",
                        not no_ci_path, f"経路なし={no_ci_path or 'なし'}"))

    no_evidence = sorted(g for g in registered
                         if not guard_results.get(g, {}).get("evidence", False))
    results.append(_hyp("H8", "全対象ガードが自身の宣言どおりexports/へ監査証跡(*.md)を出力済み",
                        not no_evidence, f"証跡なし={no_evidence or 'なし'}"))

    results.append(_hyp("H9", "AGENTS.mdのcloseoutにプリフライトコマンドが記載(手順ドリフト0)",
                        bool(closeout_has_preflight),
                        f"AGENTS.md記載={'あり' if closeout_has_preflight else 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp("H10", "プリフライト全体が完全・整合(ドリフト0)",
                        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))
    return results


def run_preflight(full: bool = False) -> dict[str, Any]:
    print(f"[*] レーン・プリフライト ({'完全モード' if full else '高速モード'})")
    print(f"[*] STEP 1: 整合ガード {len(GUARD_REGISTRY)} 件を実行中...")
    guard_results = run_guards()

    if full:
        print("[*] STEP 2: 全自動テストスイートを実行中 (数分かかります)...")
        pytest_result = run_pytest()
        print(f"  failed={pytest_result['failed']}, errors={pytest_result['errors']}, "
              f"collected={pytest_result['collected']}")
    else:
        print("[*] STEP 2: 高速モードのためテストはスキップ (push前は --full を使用)")
        pytest_result = {"skipped": True, "failed": 0, "errors": 0, "collected": 0}

    hyps = evaluate(
        discovered=discover_guards(),
        registry=GUARD_REGISTRY,
        guard_results=guard_results,
        pytest_result=pytest_result,
        imported_guards=find_imported_guards(),
        test_file_count=count_test_files(),
        closeout_has_preflight=closeout_documents_preflight(),
        exempt=EXEMPT_GUARDS,
    )
    return {
        "task": "T894",
        "mode": "full" if full else "fast",
        "guard_count": len(GUARD_REGISTRY),
        "exempt_count": len(EXEMPT_GUARDS),
        "test_file_count": count_test_files(),
        "guard_results": guard_results,
        "pytest": pytest_result,
        "hypotheses": hyps,
        "all_passed": all(h["passed"] for h in hyps),
    }


def render_markdown(report: dict[str, Any]) -> str:
    mode = "完全モード(ガード+全テスト)" if report.get("mode") == "full" else "高速モード(ガードのみ)"
    lines = [
        "# レーン・プリフライト監査 (T894)",
        "",
        f"- 実行モード: **{mode}**",
        f"- 対象ガード: **{report['guard_count']}** / 対象外: **{report.get('exempt_count', 0)}** "
        f"/ テストファイル: **{report['test_file_count']}**",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for h in report["hypotheses"]:
        mark = "✅" if h["passed"] else "❌"
        lines.append(f"| {h['id']} | {h['title']} | {mark} | {h['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    configure_utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="全自動テストスイートも実行する (push/クローズアウト前)")
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = run_preflight(full=args.full)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print()
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
