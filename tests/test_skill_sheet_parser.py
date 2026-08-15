"""Test suite for Skill Sheet Parser module (T965)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from skill_sheet_parser import parse_skill_sheet_text

def test_parse_skill_sheet_text_basic():
    sample_text = """
    氏名：田中 雄大
    経験年数：5年
    希望単価：80万円
    稼働可能日：即日
    【スキル】
    Python, FastAPI, Docker, AWS, PostgreSQL
    """
    res = parse_skill_sheet_text(sample_text)
    assert res["status"] == "success"
    assert res["engineer_name"] == "田中 雄大"
    assert res["experience_years"] == 5
    assert res["desired_rate_man_yen"] == 80
    assert "Python" in res["detected_skills"]
    assert "AWS" in res["detected_skills"]

def test_parse_skill_sheet_fallback():
    res = parse_skill_sheet_text("簡単な経歴書テキストです。")
    assert res["status"] == "success"
    assert res["experience_years"] >= 1
    assert len(res["detected_skills"]) >= 1
