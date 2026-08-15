"""Unit tests for P0 (contract_type/privacy), P1 (skill synonyms), P2 (AI proposal endpoint)."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sales_email_match import SKILL_SYNONYMS, detect_contract_type, skill_key
from app import app

client = TestClient(app)


def test_p1_skill_synonyms_normalization():
    assert skill_key("React.js") == "react"
    assert skill_key("TS") == "typescript"
    assert skill_key("Py") == "python"
    assert skill_key("JS") == "javascript"
    assert skill_key("K8s") == "kubernetes"
    assert skill_key("Postgres") == "postgresql"
    assert skill_key("GCP") == "google cloud"


def test_p0_detect_contract_type():
    assert detect_contract_type("SESでの準委任契約案件") == "準委任"
    assert detect_contract_type("特定派遣での常駐要員") == "派遣"
    assert detect_contract_type("受託システム開発の請負契約") == "請負"
    assert detect_contract_type("正社員の直接雇用採用") == "正社員/契約社員"


def test_p2_proposal_endpoint():
    response = client.post(
        "/api/sales-email/proposal",
        json={
            "project_title": "Java/React基幹システム開発",
            "talent_label": "T-8091 (Java/React 5年)",
            "score": 92,
            "matched_skills": ["Java", "React"],
            "contract_type": "準委任",
            "remote_type": "フルリモート"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Java/React基幹システム開発" in data["subject"]
    assert "T-8091" in data["proposal_text"]
    assert "適合度: 92%" in data["proposal_text"]
