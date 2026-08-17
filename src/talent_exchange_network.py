#!/usr/bin/env python3
"""Inter-Enterprise Talent Exchange Network Module (T983 - Action 20).

Enables trusted partner SES/SIer companies to cross-share surplus engineer profiles and open job orders,
automatically calculating take-rate platform fees (5-10%) and GMV settlement ledgers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ExchangeListing:
    listing_id: str
    owner_company_id: str
    listing_type: str  # "AVAILABLE_ENGINEER" or "OPEN_PROJECT"
    title_masked: str
    skills: List[str]
    monthly_rate_man_yen: int
    is_active: bool = True


@dataclass
class ExchangeMatchDeal:
    deal_id: str
    project_listing_id: str
    engineer_listing_id: str
    supplier_company_id: str
    client_company_id: str
    contract_monthly_fee_man_yen: int
    platform_take_rate_pct: float  # e.g., 7.5%
    platform_fee_monthly_yen: int
    supplier_revenue_monthly_yen: int
    deal_status: str  # "MATCHED", "IN_CONTRACT", "COMPLETED"


class TalentExchangeNetwork:
    def __init__(self, platform_take_rate_pct: float = 7.5) -> None:
        self.take_rate_pct = platform_take_rate_pct
        self.listings: List[ExchangeListing] = []
        self.deals: List[ExchangeMatchDeal] = []

    def post_listing(
        self,
        company_id: str,
        listing_type: str,
        title_masked: str,
        skills: List[str],
        monthly_rate_man_yen: int
    ) -> ExchangeListing:
        listing_id = f"EX-{int(time.time())}-{len(self.listings) + 1}"
        item = ExchangeListing(
            listing_id=listing_id,
            owner_company_id=company_id,
            listing_type=listing_type,
            title_masked=title_masked,
            skills=skills,
            monthly_rate_man_yen=monthly_rate_man_yen,
            is_active=True
        )
        self.listings.append(item)
        return item

    def match_and_close_deal(
        self,
        project_listing: ExchangeListing,
        engineer_listing: ExchangeListing,
        agreed_rate_man_yen: Optional[int] = None
    ) -> ExchangeMatchDeal:
        fee_man_yen = agreed_rate_man_yen or engineer_listing.monthly_rate_man_yen
        total_monthly_yen = fee_man_yen * 10000

        platform_fee = round(total_monthly_yen * (self.take_rate_pct / 100.0))
        supplier_rev = total_monthly_yen - platform_fee

        deal_id = f"DEAL-EX-{int(time.time())}"
        deal = ExchangeMatchDeal(
            deal_id=deal_id,
            project_listing_id=project_listing.listing_id,
            engineer_listing_id=engineer_listing.listing_id,
            supplier_company_id=engineer_listing.owner_company_id,
            client_company_id=project_listing.owner_company_id,
            contract_monthly_fee_man_yen=fee_man_yen,
            platform_take_rate_pct=self.take_rate_pct,
            platform_fee_monthly_yen=platform_fee,
            supplier_revenue_monthly_yen=supplier_rev,
            deal_status="IN_CONTRACT"
        )
        self.deals.append(deal)
        return deal

    def get_gmv_summary(self) -> Dict[str, Any]:
        total_gmv_yen = sum(d.contract_monthly_fee_man_yen * 10000 for d in self.deals)
        total_platform_revenue_yen = sum(d.platform_fee_monthly_yen for d in self.deals)

        return {
            "total_active_listings_count": len([l for l in self.listings if l.is_active]),
            "total_closed_deals_count": len(self.deals),
            "monthly_gmv_yen": total_gmv_yen,
            "monthly_platform_revenue_yen": total_platform_revenue_yen,
            "take_rate_pct": self.take_rate_pct,
            "currency": "JPY"
        }
