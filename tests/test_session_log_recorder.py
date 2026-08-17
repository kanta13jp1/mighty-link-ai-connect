# -*- coding: utf-8 -*-
"""
Unit tests for Antigravity Session Log Recorder (record_session_log.py).
"""

import json
from pathlib import Path
import pytest
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from record_session_log import parse_transcript, record_session_log


def test_session_logger_creates_files(tmp_path):
    """Verify session log recording creates log files without exception."""
    record_session_log()
    docs_dir = PROJECT_ROOT / "docs"
    assert (docs_dir / "SESSION_LOG.md").exists(), "docs/SESSION_LOG.md must exist"
    assert (docs_dir / "sessions").exists(), "docs/sessions directory must exist"
