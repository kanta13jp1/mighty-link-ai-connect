# -*- coding: utf-8 -*-
"""
Tests for Obsidian development workflow documentation and vault structure generation.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_knowledge_flow_demo import build_obsidian_vault, OBSIDIAN_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = PROJECT_ROOT / "docs" / "OBSIDIAN_DEVELOPMENT_WORKFLOW.md"


def test_obsidian_workflow_doc_exists_and_valid():
    """Verify that docs/OBSIDIAN_DEVELOPMENT_WORKFLOW.md exists and contains required sections."""
    assert DOC_PATH.exists(), "docs/OBSIDIAN_DEVELOPMENT_WORKFLOW.md must exist"
    content = DOC_PATH.read_text(encoding="utf-8")
    
    assert "T929" in content, "Doc must reference WBS T929"
    assert "4 層構造" in content or "4-Tier" in content or "4層構造" in content, "Doc must define 4-Tier Knowledge Architecture"
    assert "00_Inbox" in content, "Doc must reference 00_Inbox"
    assert "10_ADR_Drafts" in content, "Doc must reference 10_ADR_Drafts"
    assert "20_Prompts" in content, "Doc must reference 20_Prompts"
    assert "30_Meetings" in content, "Doc must reference 30_Meetings"
    assert "40_Canvas" in content, "Doc must reference 40_Canvas"
    assert "WikiLink" in content, "Doc must explain WikiLinks"
    assert "CAUTION" in content or "IMPORTANT" in content, "Doc must highlight security rules"


def test_generate_obsidian_vault_structure():
    """Verify that build_obsidian_vault creates 4-tier subdirectories."""
    summary = {
        "total": 367,
        "done": 356,
        "active": 0,
        "todo": 11,
        "completion_rate": 97,
    }
    build_obsidian_vault(summary)
    
    assert (OBSIDIAN_DIR / "00_Inbox" / "README.md").exists()
    assert (OBSIDIAN_DIR / "10_ADR_Drafts" / "README.md").exists()
    assert (OBSIDIAN_DIR / "20_Prompts" / "README.md").exists()
    assert (OBSIDIAN_DIR / "30_Meetings" / "README.md").exists()
    assert (OBSIDIAN_DIR / "40_Canvas" / "README.md").exists()
    assert (OBSIDIAN_DIR / "Mighty Skill-Bridge Home.md").exists()
