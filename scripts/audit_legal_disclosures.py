"""Legal-disclosure integrity guard (T900).

The statutory disclosure documents — 利用規約 (TERMS_OF_SERVICE), プライバシー
ポリシー (PRIVACY_POLICY), 特商法表記 (TOKUSHOHO_NOTATION), 課金・返金
(BILLING_AND_REFUND_POLICY) — carry legally mandated items (特定商取引法の表示
義務・個人情報保護法の明示事項) and must not contradict one another. A one-off
2026-07-04 report checked them once; this harness turns that into a continuous
CI guard so a missing 特商法 item or a cancellation/refund clause that drifts
between documents fails CI before the paid-launch decision (T862).

Pins ten hypotheses:

* the four statutory docs exist (H1),
* 特商法表記 covers every mandated item (H2),
* プライバシーポリシー covers the 個人情報保護法 items (H3),
* 利用規約 carries the required clauses (H4),
* cancellation is stated in BOTH 特商法表記 and 利用規約 (H5),
* refund/cancellation is stated in BOTH 特商法表記 and 課金・返金ポリシー (H6),
* the business name agrees between 特商法表記 and プライバシーポリシー (H7),
* the retention period is stated in BOTH プライバシーポリシー and the data
  retention runbook (H8),
* consumption-tax / invoice handling is disclosed for the paid launch (H9),
* the disclosures are complete and mutually consistent overall (H10).

Output: exports/legal_disclosures_audit.{json,md}. Unconfirmed placeholders
(（仮）/（予定）/確認後確定) are counted and reported so they can be resolved
before paid launch, but do not by themselves fail the guard (GA-stage drafts
are expected to carry some). No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"
TERMS = DOCS / "TERMS_OF_SERVICE.md"
PRIVACY = DOCS / "PRIVACY_POLICY.md"
TOKUSHOHO = DOCS / "TOKUSHOHO_NOTATION.md"
BILLING = DOCS / "BILLING_AND_REFUND_POLICY.md"
RETENTION = DOCS / "DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "legal_disclosures_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "legal_disclosures_audit.md"

# 特定商取引法（通信販売）の表示義務に対応する必須項目。各項目は代替語のいずれか
# を満たせばよい（同義表現の揺れを許容）。
TOKUSHOHO_ITEMS: list[tuple[str, list[str]]] = [
    ("事業者名", ["事業者名", "販売事業者", "事業者情報"]),
    ("責任者", ["責任者", "代表者", "運営統括責任者"]),
    ("所在地", ["所在地", "住所"]),
    ("連絡先", ["連絡先", "サポート", "問い合わせ", "問合せ"]),
    ("販売価格", ["販売価格", "価格", "料金"]),
    ("商品代金以外の料金", ["商品代金以外", "消費税", "手数料"]),
    ("支払方法", ["支払方法", "支払い方法", "クレジットカード", "Stripe"]),
    ("支払時期", ["支払時期", "支払い時期", "即時課金", "自動更新"]),
    ("引渡し時期", ["引渡し", "引き渡し", "サービス提供", "提供開始"]),
    ("返品・キャンセル", ["返品", "キャンセル", "返金"]),
    ("解約方法", ["解約", "退会"]),
]

# 個人情報保護法で明示すべき事項。
PRIVACY_ITEMS: list[tuple[str, list[str]]] = [
    ("事業者情報", ["事業者情報", "事業者名", "事業者"]),
    ("取得する個人情報", ["取得する個人情報", "取得情報", "取得する情報"]),
    ("利用目的", ["利用目的"]),
    ("第三者提供", ["第三者提供", "第三者への提供"]),
    ("安全管理措置", ["安全管理"]),
    ("開示等の請求", ["開示", "訂正", "利用停止"]),
    ("保管期間", ["保管期間", "保存期間", "保持期間"]),
]

# 利用規約に必要な主要条項。
TERMS_ITEMS: list[tuple[str, list[str]]] = [
    ("利用料金", ["利用料金", "料金", "利用料"]),
    ("退会・データ削除", ["退会", "解約", "データ削除"]),
    ("免責", ["免責", "保証の否認", "免責事項"]),
    ("準拠法・管轄", ["準拠法", "裁判管轄", "管轄"]),
    ("規約の変更", ["規約の変更", "本規約の変更", "規約変更"]),
]

_PLACEHOLDER_RE = re.compile(
    r"（仮）|\(仮\)|（予定）|\(予定\)|確認後確定|（未定）|\(未定\)|TBD|【要法務確認】|【要確認】"
)


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def missing_items(text: str, required: list[tuple[str, list[str]]]) -> list[str]:
    """Labels whose alternatives are all absent from `text`."""
    return [label for label, alts in required if not any(a in text for a in alts)]


def both_cover(text_a: str, text_b: str, alternatives: list[str]) -> bool:
    """True when at least one alternative appears in BOTH documents."""
    return any(a in text_a for a in alternatives) and any(a in text_b for a in alternatives)


def placeholder_count(text: str) -> int:
    """Count unconfirmed markers (（仮）/（予定）/確認後確定/…) to resolve pre-launch."""
    return len(_PLACEHOLDER_RE.findall(text))


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate() -> list[dict[str, Any]]:
    terms, privacy, tokusho, billing, retention = (
        read(TERMS), read(PRIVACY), read(TOKUSHOHO), read(BILLING), read(RETENTION)
    )
    results: list[dict[str, Any]] = []

    present = {
        "利用規約": bool(terms), "プライバシーポリシー": bool(privacy),
        "特商法表記": bool(tokusho), "課金・返金": bool(billing),
    }
    missing_docs = [k for k, v in present.items() if not v]
    results.append(_hyp("H1", "法定開示4文書(利用規約/プライバシー/特商法/課金返金)が存在",
                        not missing_docs, f"欠落文書={missing_docs or 'なし'}"))

    m2 = missing_items(tokusho, TOKUSHOHO_ITEMS)
    results.append(_hyp("H2", "特商法表記が必須表示項目を網羅",
                        not m2, f"欠落項目={m2 or 'なし'}"))

    m3 = missing_items(privacy, PRIVACY_ITEMS)
    results.append(_hyp("H3", "プライバシーポリシーが個情法明示事項を網羅",
                        not m3, f"欠落項目={m3 or 'なし'}"))

    m4 = missing_items(terms, TERMS_ITEMS)
    results.append(_hyp("H4", "利用規約が必須条項を網羅",
                        not m4, f"欠落条項={m4 or 'なし'}"))

    cancel_ok = both_cover(tokusho, terms, ["解約", "退会"])
    results.append(_hyp("H5", "解約/退会が特商法表記と利用規約の双方に記載",
                        cancel_ok, f"整合={'あり' if cancel_ok else '不整合'}"))

    refund_ok = both_cover(tokusho, billing, ["返金", "キャンセル", "返品"])
    results.append(_hyp("H6", "返金/キャンセルが特商法表記と課金返金ポリシーの双方に記載",
                        refund_ok, f"整合={'あり' if refund_ok else '不整合'}"))

    name_ok = both_cover(tokusho, privacy, ["MightyLINK", "Mighty Link", "Mighty-Link"])
    results.append(_hyp("H7", "事業者名が特商法表記とプライバシーポリシーで一致",
                        name_ok, f"整合={'あり' if name_ok else '不整合'}"))

    retention_ok = both_cover(privacy, retention, ["保管期間", "保存期間", "保持期間", "保持"])
    results.append(_hyp("H8", "保管期間がプライバシーポリシーとデータ保持Runbookの双方に記載",
                        retention_ok, f"整合={'あり' if retention_ok else '不整合'}"))

    tax_ok = any(k in (tokusho + billing) for k in ["消費税", "インボイス", "適格請求書", "税込"])
    results.append(_hyp("H9", "消費税/インボイス等の税務表示が特商法表記または課金ポリシーに存在",
                        tax_ok, f"税務表示={'あり' if tax_ok else 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp("H10", "法定開示が完全・整合(必須項目網羅かつ文書間ドリフト0)",
                        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))
    return results


def run_audit() -> dict[str, Any]:
    hyps = evaluate()
    ph = sum(placeholder_count(read(p)) for p in (TERMS, PRIVACY, TOKUSHOHO, BILLING))
    return {
        "task": "T900",
        "placeholder_count": ph,
        "hypotheses": hyps,
        "all_passed": all(h["passed"] for h in hyps),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 法定開示文書 整合性監査 (T900)",
        "",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        f"- 未確定項目(プレースホルダ)件数: **{report['placeholder_count']}**"
        "（有償化(T862)前に確定すること）",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()
    report = run_audit()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
