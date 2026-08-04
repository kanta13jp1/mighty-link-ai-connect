"""Tests for Sales Email AI matching prompt & fallback Japanese wording quality (T927)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app import build_fallback_match  # noqa: E402


def test_build_fallback_match_japanese_politeness() -> None:
    """Verify build_fallback_match generates polite, natural Japanese sentences."""
    engineer_text = "Python, FastAPI, Supabaseの開発経験があるバックエンドエンジニア。"
    job_text = "PythonとFastAPIを使ったWebアプリケーション開発案件。"

    result = build_fallback_match(engineer_text, job_text, "test_fallback")

    assert "summary" in result
    assert "qa" in result
    assert "roadmap_week1" in result

    summary = result["summary"]
    assert "適合度" in summary
    assert "です。" in summary or "でした。" in summary

    qa = result["qa"]
    assert len(qa) >= 1
    for q in qa:
        assert "question" in q


def test_build_fallback_match_empty_skills_graceful_japanese() -> None:
    """Verify build_fallback_match handles empty skills gracefully without raw placeholders."""
    result = build_fallback_match("", "", "fallback_empty")
    summary = result["summary"]
    assert "400 Bad Request" not in summary
    assert "TypeError" not in summary
    assert "適合度" in summary
