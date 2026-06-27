import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import diagnose_custom_domain_dns as diag


def test_is_nxdomain_matches_public_resolver_messages():
    assert diag.is_nxdomain("dns.google can't find mightylink-app.com: Non-existent domain")
    assert diag.is_nxdomain("status: NXDOMAIN")
    assert not diag.is_nxdomain("Name: mightylink-app.com\nAddress: 199.36.158.100")


def test_analyze_flags_client_hold_and_public_dns_nxdomain():
    rdap = {
        "status": ["client hold"],
        "nameservers": [{"ldhName": "01.DNSV.JP"}, {"ldhName": "02.DNSV.JP"}],
    }
    dns_results = [
        {"query_type": "NS", "server": "8.8.8.8", "nxdomain": True},
        {"query_type": "NS", "server": "1.1.1.1", "nxdomain": True},
    ]

    result = diag.analyze(rdap, dns_results)

    assert result["status"] == "blocked"
    assert "rdap_client_hold" in result["blockers"]
    assert "public_dns_nxdomain" in result["blockers"]
    assert result["rdap_nameservers"] == ["01.DNSV.JP", "02.DNSV.JP"]


def test_analyze_allows_recheck_when_no_blocker_is_seen():
    rdap = {
        "status": ["ok"],
        "nameservers": [{"ldhName": "01.DNSV.JP"}],
    }
    dns_results = [
        {"query_type": "NS", "server": "8.8.8.8", "nxdomain": False},
        {"query_type": "NS", "server": "1.1.1.1", "nxdomain": False},
    ]

    result = diag.analyze(rdap, dns_results)

    assert result["status"] == "ready_for_uptime_recheck"
    assert result["blockers"] == []
