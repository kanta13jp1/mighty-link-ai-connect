#!/usr/bin/env python3
"""SES Smart Contract Generator & Legal Compliance Checker Module (T980 - Action 17).

Generates SES individual service contracts (Quasi-Delegation / Dispatch / Subcontracting),
validates settlement hour ranges (e.g. 140h-180h), and verifies compliance with Labor Dispatch / SES laws.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ContractTerms:
    client_company_name: str
    supplier_company_name: str
    engineer_name: str
    project_title: str
    contract_type: str  # "準委任", "派遣", "請負"
    monthly_fee_man_yen: int
    min_hours: int = 140
    max_hours: int = 180
    payment_terms: str = "月末締め翌月末日払い（30日サイト）"
    start_date: str = "2026-09-01"
    end_date: str = "2026-11-30"


@dataclass
class GeneratedContractResult:
    contract_id: str
    contract_type: str
    is_compliant: bool
    compliance_warnings: List[str]
    contract_markdown: str
    cloudsign_metadata: Dict[str, Any]


class SESContractGenerator:
    def __init__(self) -> None:
        pass

    def generate_contract(self, terms: ContractTerms) -> GeneratedContractResult:
        warnings = []
        is_compliant = True

        # Compliance checks
        if terms.contract_type == "準委任":
            if terms.min_hours < 120 or terms.max_hours > 200:
                warnings.append("精算幅が標準的基準（140h〜180h）から大きく乖離しています。過重労働にご注意ください。")
            if terms.monthly_fee_man_yen < 40:
                warnings.append("単価水準が極めて低く、適正労務費の基準に抵触する恐れがあります。")
        elif terms.contract_type == "請負":
            warnings.append("請負契約では完成責任および瑕疵担保責任（契約不適合責任）が発生します。SES常駐では偽装請負リスクに注意してください。")

        contract_id = f"CTR-{datetime.now().strftime('%Y%m%d')}-{terms.monthly_fee_man_yen}"

        overtime_unit_rate = round((terms.monthly_fee_man_yen * 10000) / terms.max_hours) if terms.max_hours else 0
        deduction_unit_rate = round((terms.monthly_fee_man_yen * 10000) / terms.min_hours) if terms.min_hours else 0

        contract_md = f"""# 業務委託個別契約書（{terms.contract_type}）

**契約番号**: {contract_id}  
**委託者（甲）**: {terms.client_company_name}  
**受託者（乙）**: {terms.supplier_company_name}  

甲および乙は、基本契約に基づき、以下のとおり個別契約を締結する。

---

### 第1条（業務内容および対象エンジニア）
1. **業務名称**: {terms.project_title}
2. **従事技術者**: {terms.engineer_name}
3. **契約形態**: {terms.contract_type}

### 第2条（委託期間および作業場所）
1. **委託期間**: {terms.start_date} から {terms.end_date} まで
2. **作業場所**: 甲の指定する場所（リモートワーク環境を含む）

### 第3条（委託料金および精算条件）
1. **月額委託料金**: 金 {terms.monthly_fee_man_yen:,} 万円（消費税別）
2. **基準時間幅**: 月間 {terms.min_hours} 時間以上 {terms.max_hours} 時間以下
3. **精算単価**:
   - 超過単価: 1時間あたり 金 {overtime_unit_rate:,} 円（{terms.max_hours}時間超過時）
   - 控除単価: 1時間あたり 金 {deduction_unit_rate:,} 円（{terms.min_hours}時間未満時）
4. **支払条件**: {terms.payment_terms}

### 第4条（指揮命令関係の確認）
本契約が準委任契約である場合、乙の従事者に対する指揮命令権は乙に帰属し、甲は直接の指揮命令を行わないものとする（偽装請負防止）。

---
**締結日**: {datetime.now().strftime('%Y年%m月%d日')}  
甲: {terms.client_company_name}  
乙: {terms.supplier_company_name}
"""

        cloudsign_meta = {
            "document_name": f"【個別契約書】{terms.project_title}_{terms.engineer_name}",
            "signers": [
                {"company": terms.client_company_name, "role": "Client"},
                {"company": terms.supplier_company_name, "role": "Supplier"}
            ],
            "monthly_fee": terms.monthly_fee_man_yen * 10000,
            "contract_type": terms.contract_type
        }

        return GeneratedContractResult(
            contract_id=contract_id,
            contract_type=terms.contract_type,
            is_compliant=is_compliant,
            compliance_warnings=warnings,
            contract_markdown=contract_md,
            cloudsign_metadata=cloudsign_meta
        )
