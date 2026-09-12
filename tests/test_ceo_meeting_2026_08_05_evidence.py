"""T911 test spec (written test-first): 8/5 社長定例の実施証跡.

T988 の再監査 (docs/PROJECT_STALL_REVIEW_2026-08-19.md) は T911 の残作業を
「8/5会議の実施有無、決定事項、確認日を正本へ記録」と定め、WBS 注記は
**「アジェンダ記載だけを承認済み証拠にしない」** と明記している。8/23 期限を
超過したまま、アジェンダの決定事項記録欄は空欄のままだった。

AI レーンが正当にできるのは「決定事項の捏造」ではなく **実施有無の客観的な
事実確認** である。本スイートはその証跡ドキュメントを固定する:

* Google Calendar を実際に照会した範囲と結果が記載されていること
* 会議が「開催された」と断定していないこと（カレンダー不在は不開催の証拠では
  あっても証明ではない）
* WBS 同期が生成したタスクイベントを会議証跡として扱っていないこと
* 決定事項は人間が確定するまで空欄のままであること
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = PROJECT_ROOT / "docs" / "meetings" / "CEO_MEETING_2026-08-05_EVIDENCE.md"
AGENDA = PROJECT_ROOT / "docs" / "meetings" / "CEO_MEETING_AGENDA_2026-08-05.md"


def _doc() -> str:
    return EVIDENCE.read_text(encoding="utf-8")


def test_evidence_doc_exists():
    assert EVIDENCE.exists(), f"missing {EVIDENCE}"


def test_records_what_was_actually_queried():
    """検証の再現性: 照会先・照会範囲・実施日が書かれていること。"""
    doc = _doc()
    assert "Google Calendar" in doc
    assert "2026-08-05" in doc
    # 照会した4カレンダーが列挙されている
    for cal in ("k-umezawa@ml-mightylink.com",
                "kobayashi-masami@ml-mightylink.com",
                "Mighty Skill-Bridge 開発計画"):
        assert cal in doc, f"照会先が未記載: {cal}"
    assert "authorized_user.json" in doc, "どの認証で照会したかを明記すること"


def test_records_the_absence_and_the_conflict():
    """中核の事実: 13:30 の定例イベントが無く、13:00-14:00 に外部予定がある。"""
    doc = _doc()
    assert "山梨銀行打ち合わせ" in doc
    assert "13:00" in doc and "14:00" in doc
    assert "13:30" in doc


def test_does_not_treat_the_wbs_sync_event_as_meeting_evidence():
    """WBS 同期が作るタスクイベントは実施証跡ではない。"""
    doc = _doc()
    assert "sync_wbs_to_calendar" in doc
    assert "実施証跡ではない" in doc or "会議証跡ではない" in doc


def test_does_not_assert_the_meeting_happened_or_invent_decisions():
    """実施の断定と決定事項の捏造をしない。"""
    doc = _doc()
    for forbidden in ("開催された。", "決定した。", "承認された。", "議事録を作成した"):
        assert forbidden not in doc, f"断定的記述は不可: {forbidden}"
    # 決定事項は人間確定待ちであることが明示されている
    assert "未確定" in doc
    assert "人間" in doc or "寛太梅澤" in doc


def test_states_the_limit_of_the_evidence():
    """カレンダー不在は不開催の『証拠』であって『証明』ではないと明記する。"""
    doc = _doc()
    assert "証明ではない" in doc or "断定できない" in doc


def test_names_the_decision_the_human_must_make():
    doc = _doc()
    assert "実施有無" in doc
    assert "確認日" in doc
    assert "T911" in doc


def test_agenda_decision_fields_remain_unfilled_by_ai():
    """AI がアジェンダの決定事項記録欄を埋めていないこと（捏造防止の実地確認）。"""
    agenda = AGENDA.read_text(encoding="utf-8")
    section = agenda.split("## 3. 決定事項記録欄")[1]
    # 各チェックボックスは未チェックで、記入欄は空白のまま
    assert "[x]" not in section.lower(), "AI が承認済みチェックを入れてはならない"
    assert section.count("______") >= 3, "記入欄が人間用に空のまま残っていること"


def test_evidence_is_linked_from_the_agenda():
    """アジェンダ単体が承認証拠と誤読されないよう相互参照する。"""
    agenda = AGENDA.read_text(encoding="utf-8")
    assert "CEO_MEETING_2026-08-05_EVIDENCE.md" in agenda


def test_no_fabricated_attendee_confirmation():
    """出席者の確認日を勝手に埋めない。"""
    doc = _doc()
    # 「確認日: 2026-..」のように具体日が確定済みとして書かれていないこと
    assert not re.search(r"確認日\s*[:：]\s*2026-\d{2}-\d{2}", doc), \
        "確認日は人間が記入するまで空欄であること"


# --------------------------------------------------------------------------- #
# 再現ツールの純粋関数 (scripts/verify_ceo_meeting_calendar_evidence.py)
# ネットワーク・認証なしで検証できる部分のみを対象にする。
# --------------------------------------------------------------------------- #
import sys  # noqa: E402

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_ceo_meeting_calendar_evidence as cal  # noqa: E402

SLOT_START = "2026-08-05T13:30:00+09:00"
SLOT_END = "2026-08-05T14:30:00+09:00"


def test_overlap_detects_the_real_conflict():
    """社長の山梨銀行打ち合わせ 13:00-14:00 は 13:30 枠と重複する。"""
    assert cal.overlaps("2026-08-05T13:00:00+09:00", "2026-08-05T14:00:00+09:00",
                        SLOT_START, SLOT_END) is True


def test_overlap_excludes_non_touching_events():
    assert cal.overlaps("2026-08-05T10:00:00+09:00", "2026-08-05T11:00:00+09:00",
                        SLOT_START, SLOT_END) is False
    # 隣接（終了と開始が一致）は重複としない
    assert cal.overlaps("2026-08-05T12:30:00+09:00", "2026-08-05T13:30:00+09:00",
                        SLOT_START, SLOT_END) is False


def test_all_day_event_does_not_crash_or_occupy_the_slot():
    """終日イベントは naive datetime になり、tz-aware な枠と比較すると
    TypeError になる。枠を占有しないものとして False を返すこと。"""
    assert cal.overlaps("2026-08-05", "2026-08-06", SLOT_START, SLOT_END) is False


def test_wbs_sync_event_is_not_counted_as_a_meeting():
    """sync_wbs_to_calendar.py 由来のイベントは実施証跡ではない。"""
    title = "【Mighty Skill-Bridge】T911 8/5(水)13:30 社長定例ミーティングの事前アジェンダ・予定確保と実施"
    assert cal.classify_event(title) == "wbs_tracker"


def test_real_meeting_title_is_a_candidate():
    assert cal.classify_event("【定例】Mighty Skill-Bridge 開発レビューミーティング") == "candidate_meeting"
    assert cal.classify_event("社長定例ミーティング") == "candidate_meeting"


def test_unrelated_event_is_other():
    assert cal.classify_event("山梨銀行打ち合わせ") == "other"
