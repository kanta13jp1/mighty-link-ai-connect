#!/usr/bin/env python3
"""Run the T770 local 100-user API load probe.

The probe uses FastAPI's ASGI app in-process so it is repeatable in CI and does
not create traffic against the CEO-shared public demo URL. Runtime data is
isolated under a temporary directory and Gemini live calls are forced off.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "exports" / "load_test_100_users_2026-07-01.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "docs" / "LOAD_TEST_100_USERS_REPORT_2026-07-01.md"
JST = timezone(timedelta(hours=9))
DEFAULT_PARSE_DELAY_SECONDS = 0.0
DEFAULT_MATCH_DELAY_SECONDS = 0.0

SLA_TARGETS_MS = {
    "p50": 1500.0,
    "p95": 3000.0,
    "p99": 8000.0,
}


@dataclass(frozen=True)
class RequestMetric:
    endpoint: str
    method: str
    status_code: int
    elapsed_ms: float
    user_id: int
    ok: bool
    error: str = ""


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((quantile / 100.0) * len(ordered)) - 1))
    return ordered[index]


def summarize_metrics(metrics: list[RequestMetric]) -> dict[str, Any]:
    grouped: dict[str, list[RequestMetric]] = defaultdict(list)
    for metric in metrics:
        grouped[metric.endpoint].append(metric)

    endpoint_summary: dict[str, dict[str, Any]] = {}
    for endpoint, items in sorted(grouped.items()):
        durations = [item.elapsed_ms for item in items]
        status_counts = Counter(str(item.status_code) for item in items)
        endpoint_summary[endpoint] = {
            "requests": len(items),
            "successes": sum(1 for item in items if item.ok),
            "errors": sum(1 for item in items if not item.ok),
            "status_counts": dict(sorted(status_counts.items())),
            "min_ms": round(min(durations), 2),
            "p50_ms": round(percentile(durations, 50), 2),
            "p95_ms": round(percentile(durations, 95), 2),
            "p99_ms": round(percentile(durations, 99), 2),
            "max_ms": round(max(durations), 2),
        }

    all_durations = [metric.elapsed_ms for metric in metrics]
    return {
        "total_requests": len(metrics),
        "total_successes": sum(1 for metric in metrics if metric.ok),
        "total_errors": sum(1 for metric in metrics if not metric.ok),
        "status_counts": dict(sorted(Counter(str(metric.status_code) for metric in metrics).items())),
        "overall": {
            "min_ms": round(min(all_durations), 2) if all_durations else 0.0,
            "p50_ms": round(percentile(all_durations, 50), 2),
            "p95_ms": round(percentile(all_durations, 95), 2),
            "p99_ms": round(percentile(all_durations, 99), 2),
            "max_ms": round(max(all_durations), 2) if all_durations else 0.0,
        },
        "by_endpoint": endpoint_summary,
    }


def evaluate_sla(summary: dict[str, Any]) -> dict[str, Any]:
    endpoint_results = {}
    for endpoint, item in summary["by_endpoint"].items():
        endpoint_results[endpoint] = {
            "p50_pass": item["p50_ms"] <= SLA_TARGETS_MS["p50"],
            "p95_pass": item["p95_ms"] <= SLA_TARGETS_MS["p95"],
            "p99_pass": item["p99_ms"] <= SLA_TARGETS_MS["p99"],
            "error_free": item["errors"] == 0,
        }

    overall = summary["overall"]
    result = {
        "targets_ms": SLA_TARGETS_MS,
        "overall_pass": (
            summary["total_errors"] == 0
            and overall["p50_ms"] <= SLA_TARGETS_MS["p50"]
            and overall["p95_ms"] <= SLA_TARGETS_MS["p95"]
            and overall["p99_ms"] <= SLA_TARGETS_MS["p99"]
        ),
        "endpoint_results": endpoint_results,
    }
    return result


def configure_test_app(tmp_root: Path):
    os.environ.setdefault("AI_FORCE_MOCK", "1")
    os.environ.setdefault("MOCK_AUTH", "1")
    os.environ.setdefault("DETERMINISTIC_PARSE_DELAY_SECONDS", str(DEFAULT_PARSE_DELAY_SECONDS))
    os.environ.setdefault("DETERMINISTIC_MATCH_DELAY_SECONDS", str(DEFAULT_MATCH_DELAY_SECONDS))
    os.environ.setdefault("RATE_LIMIT_ENABLED", "1")
    os.environ.setdefault("RATE_LIMIT_MAX_REQUESTS", "100000")
    os.environ.setdefault("RATE_LIMIT_AUTH_MAX_REQUESTS", "100000")
    os.environ.setdefault("RATE_LIMIT_EXPENSIVE_MAX_REQUESTS", "100000")
    os.environ.setdefault("GEMINI_API_KEY", "")
    os.environ.setdefault("DATABASE_URL", "")

    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    import app as app_module  # noqa: PLC0415

    data_dir = tmp_root / "data"
    audit_dir = data_dir / "audit"
    exports_dir = tmp_root / "exports"
    data_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    app_module.DATA_DIR = str(data_dir)
    app_module.EXPORTS_DIR = str(exports_dir)
    app_module.AUDIT_DIR = str(audit_dir)
    app_module.AUDIT_LOG_FILE = str(audit_dir / "ai_audit.jsonl")
    app_module.EXTERNAL_API_USAGE_LOG_FILE = str(data_dir / "external_api_usage.jsonl")
    app_module.AI_FORCE_MOCK = True
    app_module.GEMINI_READY = False
    app_module.DETERMINISTIC_PARSE_DELAY_SECONDS = DEFAULT_PARSE_DELAY_SECONDS
    app_module.DETERMINISTIC_MATCH_DELAY_SECONDS = DEFAULT_MATCH_DELAY_SECONDS
    app_module.DATABASE_URL = ""
    app_module.USE_SUPABASE = False
    app_module.SUPABASE_SDK_ACTIVE = False
    app_module.RATE_LIMIT_ENABLED = True
    app_module.RATE_LIMIT_MAX_REQUESTS = 100000
    app_module.RATE_LIMIT_AUTH_MAX_REQUESTS = 100000
    app_module.RATE_LIMIT_EXPENSIVE_MAX_REQUESTS = 100000
    app_module.api_rate_limiter.reset()
    app_module.init_db()

    return app_module


async def timed_request(client, user_id: int, method: str, endpoint: str, **kwargs: Any) -> RequestMetric:
    started = time.perf_counter()
    status_code = 0
    error = ""
    try:
        response = await client.request(method, endpoint, **kwargs)
        status_code = response.status_code
        ok = 200 <= response.status_code < 400
        if not ok:
            error = response.text[:240]
    except Exception as exc:  # pragma: no cover - defensive runtime capture
        ok = False
        error = str(exc)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return RequestMetric(endpoint=endpoint, method=method, status_code=status_code, elapsed_ms=elapsed_ms, user_id=user_id, ok=ok, error=error)


async def run_user_flow(client, user_id: int, legal_consent_version: str) -> list[RequestMetric]:
    user_ip = f"203.0.113.{(user_id % 250) + 1}"
    headers = {"X-Forwarded-For": user_ip}
    engineer_text = (
        f"氏名: 負荷試験ユーザー{user_id}\n"
        "スキル: Python, FastAPI, Supabase, Firebase, SQL\n"
        "経験: API設計、運用監視、顧客向けSaaS改善"
    )
    job_text = (
        "職種: Firebase / Supabase バックエンドエンジニア\n"
        "必須要件: Python, FastAPI, SQL, 運用監視\n"
        "歓迎: Firebase Hosting, Cloud Functions, Supabase Connection Pooler"
    )
    consent = {
        "legal_consent_accepted": "true",
        "legal_consent_version": legal_consent_version,
    }

    metrics = [
        await timed_request(client, user_id, "GET", "/api/health", headers=headers),
        await timed_request(
            client,
            user_id,
            "POST",
            "/api/parse",
            headers=headers,
            data={"text": engineer_text, "doc_type": "engineer", **consent},
        ),
        await timed_request(
            client,
            user_id,
            "POST",
            "/api/match",
            headers=headers,
            json={
                "engineer_content": engineer_text,
                "job_content": job_text,
                "legal_consent_accepted": True,
                "legal_consent_version": legal_consent_version,
            },
        ),
    ]
    return metrics


async def run_probe(app_module, concurrent_users: int) -> tuple[list[RequestMetric], float]:
    import httpx  # noqa: PLC0415

    transport = httpx.ASGITransport(app=app_module.app)
    started = time.perf_counter()
    async with httpx.AsyncClient(transport=transport, base_url="http://load.local", timeout=30.0) as client:
        nested = await asyncio.gather(
            *(run_user_flow(client, user_id, app_module.LEGAL_CONSENT_VERSION) for user_id in range(1, concurrent_users + 1))
        )
    elapsed_seconds = time.perf_counter() - started
    return [metric for user_metrics in nested for metric in user_metrics], elapsed_seconds


def build_report(concurrent_users: int, keep_tmp: bool) -> dict[str, Any]:
    tmp_root = Path(tempfile.mkdtemp(prefix="mighty_link_t770_load_"))
    try:
        app_module = configure_test_app(tmp_root)
        captured_logs = io.StringIO()
        with contextlib.redirect_stdout(captured_logs):
            metrics, elapsed_seconds = asyncio.run(run_probe(app_module, concurrent_users))
        captured_log_lines = len([line for line in captured_logs.getvalue().splitlines() if line.strip()])
        summary = summarize_metrics(metrics)
        sla = evaluate_sla(summary)
        return {
            "task_id": "T858",
            "baseline_task_id": "T770",
            "generated_at_jst": datetime.now(JST).isoformat(timespec="seconds"),
            "scenario": {
                "concurrent_users": concurrent_users,
                "requests_per_user": 3,
                "total_elapsed_seconds": round(elapsed_seconds, 3),
                "target": "In-process FastAPI ASGI probe with isolated SQLite fallback DB, mock AI mode, and per-user forwarded IPs.",
                "endpoints": ["GET /api/health", "POST /api/parse", "POST /api/match"],
                "deterministic_parse_delay_seconds": app_module.DETERMINISTIC_PARSE_DELAY_SECONDS,
                "deterministic_match_delay_seconds": app_module.DETERMINISTIC_MATCH_DELAY_SECONDS,
                "captured_internal_log_lines": captured_log_lines,
            },
            "summary": summary,
            "sla": sla,
            "scaling_policy": {
                "firebase_functions": [
                    "Set function-level maxInstances before public paid launch so burst traffic cannot overwhelm Supabase.",
                    "Use minInstances only after cold-start evidence shows user-facing P95 degradation.",
                    "Keep CPU-heavy AI work inside request lifecycle or move it to an explicit queue; do not rely on post-response background work.",
                ],
                "supabase": [
                    "Use the Supabase/Supavisor connection pooler for Firebase/serverless traffic.",
                    "Keep per-instance DB pools small and scale through pooler capacity, not unbounded function connections.",
                    "T782 remains the deeper read-replica and pool-size optimization task for real Supabase load validation.",
                ],
                "ai_and_rate_limits": [
                    "Preserve deterministic fallback and external API circuit breakers for Gemini/Seedance quota safety.",
                    "Keep per-client rate limiting enabled at the app edge; production load tests must use realistic distributed client IDs.",
                ],
            },
            "tmp_root": str(tmp_root) if keep_tmp else None,
            "errors": [
                {
                    "endpoint": metric.endpoint,
                    "user_id": metric.user_id,
                    "status_code": metric.status_code,
                    "error": metric.error,
                }
                for metric in metrics
                if not metric.ok
            ][:20],
        }
    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_root, ignore_errors=True)


def write_json(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown_legacy_t770(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    scenario = report["scenario"]
    sla = report["sla"]
    lines = [
        "# T770 100同時ユーザー負荷テスト結果とスケーリング方針",
        "",
        f"- 生成日時: {report['generated_at_jst']}",
        "- 対応WBS: T770",
        "- 関連リリース判定: PUBLIC-10",
        f"- 判定: {'PASS' if sla['overall_pass'] else 'FAIL'}",
        f"- シナリオ: {scenario['concurrent_users']}同時ユーザー x {scenario['requests_per_user']}リクエスト",
        f"- 総処理時間: {scenario['total_elapsed_seconds']} 秒",
        "- 対象: `GET /api/health`, `POST /api/parse`, `POST /api/match`",
        "- 注意: CEO共有URLへ負荷をかけないため、FastAPI ASGIアプリをローカルプロセス内で実行し、SQLite/監査ログは一時ディレクトリへ隔離した。Gemini live call は `AI_FORCE_MOCK=1` で無効化した。",
        "",
        "## SLA照合",
        "",
        "| 指標 | 目標 | 実測 | 判定 |",
        "| --- | ---: | ---: | --- |",
        f"| P50 | <= {SLA_TARGETS_MS['p50']:.0f} ms | {summary['overall']['p50_ms']} ms | {'PASS' if summary['overall']['p50_ms'] <= SLA_TARGETS_MS['p50'] else 'FAIL'} |",
        f"| P95 | <= {SLA_TARGETS_MS['p95']:.0f} ms | {summary['overall']['p95_ms']} ms | {'PASS' if summary['overall']['p95_ms'] <= SLA_TARGETS_MS['p95'] else 'FAIL'} |",
        f"| P99 | <= {SLA_TARGETS_MS['p99']:.0f} ms | {summary['overall']['p99_ms']} ms | {'PASS' if summary['overall']['p99_ms'] <= SLA_TARGETS_MS['p99'] else 'FAIL'} |",
        f"| エラー | 0 件 | {summary['total_errors']} 件 | {'PASS' if summary['total_errors'] == 0 else 'FAIL'} |",
        "",
        "## エンドポイント別結果",
        "",
        "| エンドポイント | 件数 | 成功 | エラー | P50 | P95 | P99 | Max | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for endpoint, item in summary["by_endpoint"].items():
        lines.append(
            f"| `{endpoint}` | {item['requests']} | {item['successes']} | {item['errors']} | "
            f"{item['p50_ms']} ms | {item['p95_ms']} ms | {item['p99_ms']} ms | {item['max_ms']} ms | "
            f"`{json.dumps(item['status_counts'], ensure_ascii=False)}` |"
        )

    if sla["overall_pass"]:
        public_10_text = [
            "本レポートにより、同時100ユーザー想定の代表API導線の負荷テストと初期スケーリング方針は完了したため、PUBLIC-10は `PASS` とする。",
            "ただし、有償一般公開そのものは、法務、課金、営業メール実接続hardening、会社アカウント移管、Firebase CI/CD、全機能UATなど残ゲート完了後に再判定する。",
        ]
    else:
        public_10_text = [
            "本レポートにより、同時100ユーザー想定の代表API導線の負荷テストと初期スケーリング方針は完了した。",
            "ただしSLA目標を満たしていないため、PUBLIC-10は `BLOCKED` のまま維持し、T858で改善と本番相当再試験を実施する。",
        ]

    lines.extend(
        [
            "",
            "## スケーリング方針",
            "",
            "### Firebase Functions / Hosting",
            "",
            "- Functionsは `maxInstances` を明示し、急なバーストでSupabase接続を枯渇させない。",
            "- `minInstances` はcold startがP95を悪化させる証跡が出た場合に限り、コスト上限とセットで設定する。",
            "- レスポンス後の暗黙バックグラウンド処理に依存せず、長時間AI処理は明示キューまたは人間レビュー導線へ分離する。",
            "",
            "### Supabase",
            "",
            "- Firebase/サーバーレス接続ではSupabase/Supavisor connection poolerを標準接続先にする。",
            "- 関数インスタンスごとのDB接続数は小さく保ち、無制限な直結接続を避ける。",
            "- T782で、実Supabase環境のpool size、リード分散、クエリ待ち時間を追加検証する。",
            "",
            "### AI・レート制限",
            "",
            "- Gemini/Seedanceの外部APIは引き続き日次上限、token上限、deterministic fallbackで保護する。",
            "- 本番負荷テスト時は実ユーザーに近い分散IP/セッションで実施し、単一IPのレート制限により誤判定しない。",
            "",
            "## PUBLIC-10 判定",
            "",
            *public_10_text,
            "",
            "## 公式ドキュメント確認メモ",
            "",
            "- Firebase Functions manage functions: https://firebase.google.com/docs/functions/manage-functions?gen=2nd",
            "- Firebase Functions tips: https://firebase.google.com/docs/functions/tips",
            "- Firebase Hosting: https://firebase.google.com/docs/hosting",
            "- Supabase connection pooler: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler",
            "- Supabase connection management: https://supabase.com/docs/guides/database/connection-management",
            "- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate",
            "- GitHub Actions: https://docs.github.com/actions",
            "- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md",
            "- Anthropic Claude Code overview: https://code.claude.com/docs/en/overview",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    """Write the T858 markdown report."""
    summary = report["summary"]
    scenario = report["scenario"]
    sla = report["sla"]

    lines = [
        "# T858 100同時ユーザー負荷SLA再試験結果",
        "",
        f"- 生成日時: {report['generated_at_jst']}",
        "- 対応WBS: T858",
        "- ベースラインWBS: T770",
        "- 関連リリース判定: PUBLIC-10",
        f"- 判定: {'PASS' if sla['overall_pass'] else 'FAIL'}",
        f"- シナリオ: {scenario['concurrent_users']}同時ユーザー x {scenario['requests_per_user']}リクエスト",
        f"- 総処理時間: {scenario['total_elapsed_seconds']} 秒",
        "- 対象: `GET /api/health`, `POST /api/parse`, `POST /api/match`",
        f"- deterministic fallback待機: parse {scenario['deterministic_parse_delay_seconds']} 秒 / match {scenario['deterministic_match_delay_seconds']} 秒",
        f"- 捕捉した内部ログ行数: {scenario['captured_internal_log_lines']} 行",
        "- 注意: CEO共有URLへ負荷をかけないため、FastAPI ASGIアプリをローカルプロセス内で実行し、SQLite/監査ログは一時ディレクトリへ隔離した。Gemini live call は `AI_FORCE_MOCK=1` で無効化した。",
        "",
        "## SLA判定",
        "",
        "| 指標 | 目標 | 実測 | 判定 |",
        "| --- | ---: | ---: | --- |",
        f"| P50 | <= {SLA_TARGETS_MS['p50']:.0f} ms | {summary['overall']['p50_ms']} ms | {'PASS' if summary['overall']['p50_ms'] <= SLA_TARGETS_MS['p50'] else 'FAIL'} |",
        f"| P95 | <= {SLA_TARGETS_MS['p95']:.0f} ms | {summary['overall']['p95_ms']} ms | {'PASS' if summary['overall']['p95_ms'] <= SLA_TARGETS_MS['p95'] else 'FAIL'} |",
        f"| P99 | <= {SLA_TARGETS_MS['p99']:.0f} ms | {summary['overall']['p99_ms']} ms | {'PASS' if summary['overall']['p99_ms'] <= SLA_TARGETS_MS['p99'] else 'FAIL'} |",
        f"| エラー | 0 件 | {summary['total_errors']} 件 | {'PASS' if summary['total_errors'] == 0 else 'FAIL'} |",
        "",
        "## エンドポイント別結果",
        "",
        "| エンドポイント | 件数 | 成功 | エラー | P50 | P95 | P99 | Max | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for endpoint, item in summary["by_endpoint"].items():
        lines.append(
            f"| `{endpoint}` | {item['requests']} | {item['successes']} | {item['errors']} | "
            f"{item['p50_ms']} ms | {item['p95_ms']} ms | {item['p99_ms']} ms | {item['max_ms']} ms | "
            f"`{json.dumps(item['status_counts'], ensure_ascii=False)}` |"
        )

    public_10_text = (
        [
            "本再試験により、100同時ユーザー想定の代表API導線はエラー0で完走し、P50/P95/P99のSLA目標を満たした。",
            "したがってPUBLIC-10は `PASS` とする。ただし、一般公開・有償ローンチは法務、課金、実メール接続、会社アカウント移管、Firebase CI/CDなど残ゲート完了後に再判定する。",
        ]
        if sla["overall_pass"]
        else [
            "本再試験はエラー0またはSLA目標のいずれかを満たしていない。",
            "PUBLIC-10は `BLOCKED` のまま維持し、追加の性能改善と本番相当再試験を実施する。",
        ]
    )

    lines.extend(
        [
            "",
            "## スケーリング方針",
            "",
            "### Firebase Functions / Hosting",
            "",
            "- Functionsは `maxInstances` を明示し、急なバーストでSupabase接続を枯渇させない。",
            "- `minInstances` はcold startがP95を悪化させる証跡が出た場合に限り、コスト上限とセットで設定する。",
            "- レスポンス後の暗黙バックグラウンド処理には依存せず、時間のかかるAI処理は明示キューまたは人間レビュー導線へ分離する。",
            "",
            "### Supabase",
            "",
            "- Firebase/サーバーレス接続ではSupabase/Supavisor connection poolerを標準接続先にする。",
            "- FunctionsインスタンスごとのDB接続数は小さく保ち、無制限の直接接続を避ける。",
            "- T782では実Supabase環境のpool size、read replica、クエリ待ち時間を追加検証する。",
            "",
            "### AI・レート制限",
            "",
            "- Gemini/Seedanceの外部APIは日次上限、token上限、deterministic fallbackで保護する。",
            "- 本番負荷テスト時は実ユーザーに近い分散IP/セッションで実施し、単一IPのレート制限により誤判定しない。",
            "",
            "## PUBLIC-10 判定",
            "",
            *public_10_text,
            "",
            "## 公式ドキュメント確認メモ",
            "",
            "- Firebase Functions manage functions: https://firebase.google.com/docs/functions/manage-functions?gen=2nd",
            "- Firebase Functions tips: https://firebase.google.com/docs/functions/tips",
            "- Firebase Hosting: https://firebase.google.com/docs/hosting",
            "- Supabase connection pooler: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler",
            "- Supabase connection management: https://supabase.com/docs/guides/database/connection-management",
            "- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate",
            "- GitHub Actions: https://docs.github.com/actions",
            "- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md",
            "- Anthropic Claude Code overview: https://code.claude.com/docs/en/overview",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the T858 100-user API load probe.")
    parser.add_argument("--concurrent-users", type=int, default=100)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--fail-on-sla", action="store_true")
    parser.add_argument("--keep-tmp", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.concurrent_users, keep_tmp=args.keep_tmp)
    write_json(args.json_report, report)
    write_markdown(args.markdown_report, report)
    print(
        "T858 load probe: "
        f"{report['scenario']['concurrent_users']} users, "
        f"{report['summary']['total_requests']} requests, "
        f"errors={report['summary']['total_errors']}, "
        f"p95={report['summary']['overall']['p95_ms']}ms, "
        f"status={'PASS' if report['sla']['overall_pass'] else 'FAIL'}"
    )
    print(f"JSON: {args.json_report}")
    print(f"Markdown: {args.markdown_report}")
    if args.fail_on_sla and not report["sla"]["overall_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
