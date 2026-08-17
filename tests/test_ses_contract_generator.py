import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ses_contract_generator import SESContractGenerator, ContractTerms


def test_ses_contract_generator_quasi_delegation():
    gen = SESContractGenerator()
    terms = ContractTerms(
        client_company_name="株式会社クライアント",
        supplier_company_name="株式会社マイティリンク",
        engineer_name="山田 太郎",
        project_title="AIエージェント基盤開発支援",
        contract_type="準委任",
        monthly_fee_man_yen=85,
        min_hours=140,
        max_hours=180
    )

    res = gen.generate_contract(terms)
    assert res.is_compliant is True
    assert "業務委託個別契約書（準委任）" in res.contract_markdown
    assert "850,000" in res.contract_markdown or "85" in res.contract_markdown
    assert res.cloudsign_metadata["monthly_fee"] == 850000
    assert len(res.compliance_warnings) == 0


def test_ses_contract_generator_warnings():
    gen = SESContractGenerator()
    terms = ContractTerms(
        client_company_name="株式会社甲",
        supplier_company_name="株式会社乙",
        engineer_name="鈴木 一郎",
        project_title="システム保守",
        contract_type="準委任",
        monthly_fee_man_yen=35,
        min_hours=100,
        max_hours=220
    )
    res = gen.generate_contract(terms)
    assert len(res.compliance_warnings) >= 1
