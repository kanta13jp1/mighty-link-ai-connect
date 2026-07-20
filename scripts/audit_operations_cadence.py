"""Operations cadence calendar guard (T907).

20 of the 46 runbooks declare a recurring obligation — daily DB backup, weekly
cost review, monthly quality report, quarterly security audit, annual secret
rotation — but the cadence lived only inside each runbook. After GA there was
no single view of "what must happen how often, by whom, and how do I confirm it
was done", so a quarterly audit could be skipped without anything failing.

This harness makes docs/OPERATIONS_CADENCE_CALENDAR.md the single view and
keeps it honest: the required minimum obligations must be covered, every linked
runbook must exist, and a runbook that declares a cadence must not be missing
from the calendar (minus a documented exclusion list for docs that merely cite
another runbook's cadence).

Pins ten hypotheses:

* the calendar exists (H1),
* it is organised by the five cadence headings (H2),
* every required minimum obligation is covered (H3),
* every runbook it links to exists on disk — no dangling (H4),
* runbooks declaring a cadence are all registered — none unregistered (H5),
* every entry names an owner (H6),
* every entry states how completion is confirmed (H7),
* the exclusion list is documented with reasons and still needed (H8),
* the calendar links only repo-relative paths (H9),
* calendar and runbooks are consistent overall (H10).

Output: exports/operations_cadence_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"
CALENDAR = DOCS / "OPERATIONS_CADENCE_CALENDAR.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "operations_cadence_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "operations_cadence_audit.md"

CADENCES = ["日次", "週次", "月次", "四半期", "年次"]

# The minimum set of recurring obligations the calendar must always carry.
# Key = label reported when missing; value = tokens that satisfy it.
REQUIRED: dict[str, list[str]] = {
    "日次バックアップ": ["バックアップ"],
    "週次コスト確認": ["コスト"],
    "月次品質レポート": ["品質レポート"],
    "四半期セキュリティ監査": ["セキュリティ監査"],
    "年次シークレット棚卸し": ["シークレット", "Secret", "secret"],
    "復旧訓練": ["復旧訓練", "リストア訓練", "DR訓練"],
}

# Runbooks that contain a cadence word but are NOT themselves a recurring
# obligation — they cite another runbook's cadence or a data volume.
EXCLUDED_RUNBOOKS: dict[str, str] = {
    "AI_SAAS_SERVICE_FREEZE_RUNBOOK.md": "月次品質レポート通知payloadに言及するのみ（凍結手順であり定期実施ではない）",
    "PRODUCTION_ROLLBACK_RUNBOOK.md": "バックアップRunbookの日次運用を参照するのみ（ロールバックは事象駆動）",
    "SALES_EMAIL_INGESTION_POC_RUNBOOK.md": "『毎日約1,000通届く』はデータ流量の説明であり実施頻度ではない",
    "FIREBASE_SUPABASE_QUOTA_ERROR_ALERT_RUNBOOK.md": "他ダッシュボードの週次/月次に言及するのみ（本体はアラート駆動の常時監視）",
    "SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md": "Slack/Notion接続の将来計画として月次/週次に言及するのみ（本体は問い合わせ駆動）",
    "DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md": "保持期間表に月次表記があるのみ（削除は請求駆動、定期点検は月次品質レポートに包含）",
    "DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md": "RPO説明で日次バックアップに言及（DR発動は事象駆動。定期の復旧訓練はカレンダーに別掲）",
    "SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md": "性能診断の定期実施はPERFORMANCE_DIAGNOSTIC…Runbookに集約（本体は参照系ダッシュボード）",
    "LOG_ROTATION_AND_RETENTION_RUNBOOK.md": "保持年限の表記であり、退避の定期実施はCOLD_STORAGE_LOG_ARCHIVE…Runbookに集約",
    "USAGE_ANALYTICS_KPI_RUNBOOK.md": "月次品質報告での確認項目（実施主体は月次品質レポート）",
    "USER_FEEDBACK_COLLECTION_RUNBOOK.md": "月次品質レポートへ転記する入力（実施主体は月次品質レポート）",
    "EXTERNAL_PENTEST_RUNBOOK.md": "四半期監査での棚卸し対象（実施主体は四半期セキュリティ監査）",
    "INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md": "日次生成はGitHub Actionsの自動実行（人手の定期作業ではない）",
}

_FREQ_RE = re.compile(r"(日次|毎日|週次|毎週|月次|毎月|四半期|年次|毎年)")
_RUNBOOK_LINK_RE = re.compile(r"\]\(([^)]*?[A-Za-z0-9_]*RUNBOOK[A-Za-z0-9_]*\.md)\)")
_ABS_LINK_RE = re.compile(r"\]\((file:///[^)]*|[A-Za-z]:[\\/][^)]*)\)")


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def cadence_sections(text: str) -> list[str]:
    """Cadence headings (## 日次 / ## 週次 / …) present in the calendar."""
    found = []
    for m in re.finditer(r"^#{2,3}\s+(.+)$", text, re.M):
        title = m.group(1).strip()
        for c in CADENCES:
            if title.startswith(c):
                found.append(c)
    return found


def calendar_runbooks(text: str) -> set[str]:
    """Runbook filenames linked from the calendar.

    Excludes the runbook *catalog* (…RUNBOOK_CATALOG.md): the calendar links it
    as a companion index, not as a cadence entry. runbook_files() excludes it
    too, so keeping this symmetric prevents that link from reading as dangling
    (the same asymmetry the T902_1 review caught in audit_runbook_catalog.py).
    """
    return {name for m in _RUNBOOK_LINK_RE.finditer(text)
            if (name := Path(m.group(1)).name) != "OPERATIONS_RUNBOOK_CATALOG.md"}


def runbook_files(docs_dir: Path = DOCS) -> set[str]:
    return {p.name for p in docs_dir.glob("*RUNBOOK*.md")
            if p.name not in {"OPERATIONS_RUNBOOK_CATALOG.md"}}


def dangling_links(linked: set[str], on_disk: set[str]) -> set[str]:
    return set(linked) - set(on_disk)


def missing_required(text: str) -> list[str]:
    """Required obligations with no matching token in the calendar."""
    return [label for label, tokens in REQUIRED.items()
            if not any(t in text for t in tokens)]


def cadence_declaring_runbooks(docs_dir: Path = DOCS) -> set[str]:
    """Runbooks whose body declares a recurring cadence."""
    out: set[str] = set()
    for name in runbook_files(docs_dir):
        if _FREQ_RE.search(read(docs_dir / name)):
            out.add(name)
    return out


def unregistered_cadence_runbooks(docs_dir: Path = DOCS) -> set[str]:
    """Cadence-declaring runbooks absent from the calendar and not excluded."""
    linked = calendar_runbooks(read(CALENDAR))
    return cadence_declaring_runbooks(docs_dir) - linked - set(EXCLUDED_RUNBOOKS)


def _entry_rows(text: str) -> list[str]:
    """Calendar table rows that link a runbook."""
    return [ln for ln in text.splitlines()
            if ln.strip().startswith("|") and _RUNBOOK_LINK_RE.search(ln)]


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(docs_dir: Path = DOCS) -> list[dict[str, Any]]:
    text = read(CALENDAR)
    results: list[dict[str, Any]] = []

    results.append(_hyp("H1", "運用カレンダーが存在する",
                        bool(text), f"カレンダー={'あり' if text else 'なし'}"))

    sections = cadence_sections(text)
    missing_sections = [c for c in CADENCES if c not in sections]
    results.append(_hyp("H2", "5頻度区分(日次/週次/月次/四半期/年次)で整理",
                        not missing_sections, f"欠落区分={missing_sections or 'なし'}"))

    miss_req = missing_required(text)
    results.append(_hyp("H3", "必須の定期義務を網羅",
                        not miss_req, f"必須項目の欠落={miss_req or 'なし'}"))

    linked = calendar_runbooks(text)
    on_disk = runbook_files(docs_dir)
    dangling = dangling_links(linked, on_disk)
    results.append(_hyp("H4", "カレンダーの全Runbookリンクが実在(切れリンク0)",
                        not dangling, f"切れリンク={sorted(dangling) or 'なし'}"))

    unreg = unregistered_cadence_runbooks(docs_dir)
    results.append(_hyp("H5", "定期実施Runbookが全てカレンダーに登録(未登録0)",
                        not unreg, f"未登録={sorted(unreg) or 'なし'}"))

    rows = _entry_rows(text)
    # owner column: a row must name a lane or 人間
    owners = ("人間", "Codex", "Claude", "Antigravity", "運用", "経理")
    no_owner = [r for r in rows if not any(o in r for o in owners)]
    results.append(_hyp("H6", "各エントリに担当が明記されている",
                        rows and not no_owner, f"担当欠落={len(no_owner)}件 / 全{len(rows)}件"))

    confirm = ("確認", "検証", "レポート", "出力", "通知", "記録", "存在")
    no_confirm = [r for r in rows if not any(c in r for c in confirm)]
    results.append(_hyp("H7", "各エントリに完了確認方法が明記されている",
                        rows and not no_confirm, f"確認方法欠落={len(no_confirm)}件"))

    stale_excl = sorted(n for n in EXCLUDED_RUNBOOKS if n not in on_disk)
    documented = all(bool(v) for v in EXCLUDED_RUNBOOKS.values())
    results.append(_hyp("H8", "除外リストが理由付きで文書化され、実在Runbookのみを指す",
                        documented and not stale_excl,
                        f"除外={len(EXCLUDED_RUNBOOKS)}件 / 実在しない除外={stale_excl or 'なし'}"))

    abs_links = _ABS_LINK_RE.findall(text)
    results.append(_hyp("H9", "リンクがリポジトリ相対(絶対パス無し)",
                        not abs_links, f"絶対パス={len(abs_links)}件"))

    prior_ok = all(r["passed"] for r in results if r["id"] in {"H1", "H2", "H3", "H4", "H5"})
    results.append(_hyp("H10", "カレンダーとRunbookが完全整合(運用抜け0)",
                        prior_ok, f"先行ドリフト={'なし' if prior_ok else 'あり'}"))

    return results


def _render_md(results: list[dict[str, Any]]) -> str:
    text = read(CALENDAR)
    ok = all(r["passed"] for r in results)
    lines = [
        "# 定期運用サイクル整合性監査 (T907)",
        "",
        f"- カレンダー掲載Runbook: **{len(calendar_runbooks(text))}本** / 定期宣言Runbook: **{len(cadence_declaring_runbooks())}本**",
        f"- 除外(言及のみ): **{len(EXCLUDED_RUNBOOKS)}本**",
        f"- 総合判定: {'✅ PASS (運用抜け0)' if ok else '❌ FAIL (運用抜けあり)'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['id']} | {r['title']} | {mark} | {r['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="定期運用サイクル一覧の網羅整合ガード (T907)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    results = evaluate()
    passed = all(r["passed"] for r in results)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps({"passed": passed, "hypotheses": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md = _render_md(results)
    args.md.write_text(md, encoding="utf-8")
    print(md)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
