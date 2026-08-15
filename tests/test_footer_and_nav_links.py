"""
Test suite to audit and verify that all footer, navigation, and documentation links
in index.html return HTTP 200 OK and render properly via FastAPI server (E2E link audit).
"""

import os
import re
import sys
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_footer_docs_links_reachability(client):
    """Verify that all docs links in footer return HTTP 200 OK."""
    index_path = os.path.join(PROJECT_ROOT, "index.html")
    assert os.path.isfile(index_path)

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find footer section
    footer_match = re.search(r'<footer[^>]*class="[^"]*site-footer[^"]*"[^>]*>(.*?)</footer>', content, re.DOTALL)
    assert footer_match is not None, "site-footer element must exist in index.html"
    footer_html = footer_match.group(1)

    # Extract hrefs starting with docs/
    doc_links = re.findall(r'href=["\'](docs/[^"\']+)["\']', footer_html)

    assert len(doc_links) >= 4, f"Expected at least 4 doc links in footer, found {len(doc_links)}"

    for doc_link in doc_links:
        # Request with leading slash
        url = "/" + doc_link.lstrip("/")
        resp = client.get(url)
        assert resp.status_code == 200, f"Expected 200 OK for {url}, got {resp.status_code}: {resp.text}"
        assert "<html" in resp.text.lower() or len(resp.text) > 0, f"Empty or invalid response for {url}"


def test_raw_markdown_docs_param(client):
    """Verify that ?raw=true returns plain markdown."""
    resp = client.get("/docs/TERMS_OF_SERVICE.md?raw=true")
    assert resp.status_code == 200
    assert "利用規約" in resp.text
    assert resp.headers["content-type"].startswith("text/markdown") or resp.headers["content-type"].startswith("text/plain")


def test_nonexistent_doc_returns_404(client):
    """Verify that nonexistent doc returns 404."""
    resp = client.get("/docs/NONEXISTENT_DOCUMENT_12345.md")
    assert resp.status_code == 404
