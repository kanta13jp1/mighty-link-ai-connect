# -*- coding: utf-8 -*-
"""
Test suite for Obsidian Knowledge Graph 100% connectivity.
Ensures zero isolated markdown files exist in the repository.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import connect_knowledge_graph as knowledge_graph
from connect_knowledge_graph import connect_all_knowledge_nodes, MASTER_GRAPH_FILE


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_master_knowledge_graph_file_exists():
    """Verify that docs/MASTER_KNOWLEDGE_GRAPH.md exists."""
    assert MASTER_GRAPH_FILE.exists(), "docs/MASTER_KNOWLEDGE_GRAPH.md must exist"


def test_collect_md_files_excludes_local_cache_directories(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    cache_dir = tmp_path / ".pytest_cache"
    docs_dir.mkdir()
    cache_dir.mkdir()
    tracked_doc = docs_dir / "README.md"
    cached_doc = cache_dir / "README.md"
    tracked_doc.write_text("# Docs\n", encoding="utf-8")
    cached_doc.write_text("# Cache\n", encoding="utf-8")
    monkeypatch.setattr(knowledge_graph, "PROJECT_ROOT", tmp_path)

    assert set(knowledge_graph.collect_md_files()) == {tracked_doc}


def test_zero_isolated_markdown_files():
    """Verify that 100% of markdown files are connected in the knowledge graph (isolated: 0)."""
    isolated = connect_all_knowledge_nodes()
    assert len(isolated) == 0, f"Expected 0 isolated files, but found {len(isolated)}: {[p.name for p in isolated]}"
