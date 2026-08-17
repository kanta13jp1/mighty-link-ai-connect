import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.meeting_fact_extractor import MeetingFactExtractor


def test_meeting_fact_extractor():
    extractor = MeetingFactExtractor()
    transcript = (
        "クライアント: 今回のポジションですが、月額85万円（税別）でお願いできればと思います。\n"
        "マイティリンク営業: 承知いたしました。稼働開始時期は9月中旬から可能ですがいかがでしょうか。\n"
        "クライアント: 助かります。勤務形態は完全フルリモートで、精算幅は140-180時間でお願いいたします。"
    )

    facts = extractor.extract_facts(transcript)
    assert facts.agreed_monthly_rate_man_yen == 85
    assert facts.agreed_start_date == "2026-09-15"
    assert facts.agreed_min_hours == 140
    assert facts.agreed_max_hours == 180
    assert "完全フルリモート" in facts.remote_condition
    assert facts.confidence_score >= 0.90
