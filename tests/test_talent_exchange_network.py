import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.talent_exchange_network import TalentExchangeNetwork


def test_talent_exchange_network_deal_flow():
    network = TalentExchangeNetwork(platform_take_rate_pct=8.0)

    # 1. Post project & engineer
    proj = network.post_listing(
        company_id="COMP_CLIENT_01",
        listing_type="OPEN_PROJECT",
        title_masked="【AI/FastAPI】自社開発基盤開発",
        skills=["Python", "FastAPI"],
        monthly_rate_man_yen=90
    )

    eng = network.post_listing(
        company_id="COMP_SUPPLIER_02",
        listing_type="AVAILABLE_ENGINEER",
        title_masked="シニアバックエンドエンジニア",
        skills=["Python", "FastAPI", "AWS"],
        monthly_rate_man_yen=90
    )

    # 2. Match and close deal
    deal = network.match_and_close_deal(proj, eng, agreed_rate_man_yen=90)

    assert deal.deal_status == "IN_CONTRACT"
    assert deal.contract_monthly_fee_man_yen == 90
    assert deal.platform_fee_monthly_yen == 72000  # 900,000 * 8%
    assert deal.supplier_revenue_monthly_yen == 828000

    # 3. GMV Summary
    summary = network.get_gmv_summary()
    assert summary["total_closed_deals_count"] == 1
    assert summary["monthly_gmv_yen"] == 900000
    assert summary["monthly_platform_revenue_yen"] == 72000
