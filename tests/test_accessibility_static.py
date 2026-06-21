import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_accessibility_static import check_index_html


def test_public_demo_accessibility_static_gate_passes():
    result = check_index_html(Path("index.html"))

    assert result["status"] == "PASS", result["failures"]
    assert result["passed"] == result["total"]
