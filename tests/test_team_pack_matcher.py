#!/usr/bin/env python3
"""Tests for Team Pack Matcher (T972)."""

import pytest
from src.team_pack_matcher import TeamPackMatcher, EngineerProfile


def test_team_pack_matcher_composition():
    matcher = TeamPackMatcher()
    result = matcher.compose_team(
        project_title="次世代AIエージェント基盤開発",
        required_roles=["PM", "Tech Lead", "Senior Dev"],
        required_skills=["Python", "FastAPI", "TypeScript", "Next.js", "Docker"]
    )

    assert len(result.members) == 3
    assert result.total_monthly_rate > 0
    assert result.overall_fit_score >= 80.0
    assert "次世代AIエージェント基盤開発" in result.recommended_proposal_text
    assert "PM主導による自走型スクラム開発体制" in result.recommended_proposal_text


def test_team_pack_matcher_custom_engineers():
    custom_pool = [
        EngineerProfile("E1", "エンジニアA", "PM", ["Agile", "Jira"], 100),
        EngineerProfile("E2", "エンジニアB", "QA", ["Playwright"], 70),
    ]
    matcher = TeamPackMatcher(engineers=custom_pool)
    result = matcher.compose_team(
        project_title="QA受託プロジェクト",
        required_roles=["PM", "QA"],
        required_skills=["Agile", "Playwright"]
    )
    assert len(result.members) == 2
    assert result.total_monthly_rate == 170
    assert result.skill_coverage_score == 100.0
