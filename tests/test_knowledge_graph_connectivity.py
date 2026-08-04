# -*- coding: utf-8 -*-
"""
Test suite for Obsidian Knowledge Graph 100% connectivity.
Ensures zero isolated markdown files exist in the repository.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from connect_knowledge_graph import connect_all_knowledge_nodes, MASTER_GRAPH_FILE


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_master_knowledge_graph_file_exists():
    """Verify that docs/MASTER_KNOWLEDGE_GRAPH.md exists."""
    assert MASTER_GRAPH_FILE.exists(), "docs/MASTER_KNOWLEDGE_GRAPH.md must exist"


def test_zero_isolated_markdown_files():
    """Verify that 100% of markdown files are connected in the knowledge graph (isolated: 0)."""
    isolated = connect_all_knowledge_nodes()
    assert len(isolated) == 0, f"Expected 0 isolated files, but found {len(isolated)}: {[p.name for p in isolated]}"
