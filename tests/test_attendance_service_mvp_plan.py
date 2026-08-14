"""Contract checks for the approved attendance-service MVP plan (T951)."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "ATTENDANCE_SERVICE_MVP_IMPLEMENTATION_PLAN.md"
WBS = ROOT / "data" / "WBS.tsv"


def test_attendance_mvp_plan_keeps_the_approved_architecture_and_security_gates() -> None:
    text = PLAN.read_text(encoding="utf-8")

    for required in (
        "外部OSSへ全面移行せず、現行の勤怠モジュールを拡張する",
        "Firebase IDトークン",
        "tenant_key",
        "idempotency_key",
        "別テナントアクセス",
        "管理ランタイムでFirebase Admin SDKが利用できない場合は503",
        "IDトークンがない、無効、期限切れ、失効済みの場合は401",
        "本番OAuth接続",
    ):
        assert required in text

    assert "T947の外部勤怠SaaS連携ドラフトは本MVPとは別スコープ" in text
    assert "mock token" in text
    assert "未認証provider API" in text


def test_attendance_mvp_wbs_has_one_completed_plan_and_four_future_milestones() -> None:
    rows = {
        columns[0]: columns
        for line in WBS.read_text(encoding="utf-8-sig").splitlines()[1:]
        if line.strip() and len(columns := line.split("\t")) >= 10
    }

    assert rows["T951"][7] == "完了"
    for task_id in ("T952", "T953", "T954", "T955"):
        assert rows[task_id][7] == "未着手"

    assert "厳格Firebase本人認証" in rows["T952"][3]
    assert "月次勤怠表示" in rows["T953"][3]
    assert "月次締め" in rows["T954"][3]
    assert "パイロットUAT" in rows["T955"][3]
