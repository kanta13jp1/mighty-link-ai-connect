#!/usr/bin/env python3
"""Team Pack Matcher Module (T972 - Action 13).

Optimizes and composes multi-engineer team assignment proposals (e.g. PM + Tech Lead + Members)
for large-scale projects and SI/entrusted development tenders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EngineerProfile:
    id: str
    name: str
    role: str  # PM, Tech Lead, Senior Dev, Junior Dev, QA, Designer
    skills: List[str]
    monthly_rate: int  # in 10,000 JPY
    availability: str = "即時"


@dataclass
class TeamCompositionResult:
    team_name: str
    members: List[EngineerProfile]
    total_monthly_rate: int
    skill_coverage_score: float
    synergy_score: float
    overall_fit_score: float
    recommended_proposal_text: str


class TeamPackMatcher:
    def __init__(self, engineers: Optional[List[EngineerProfile]] = None) -> None:
        self.engineers = engineers or self._get_default_talent_pool()

    def _get_default_talent_pool(self) -> List[EngineerProfile]:
        return [
            EngineerProfile("ENG-PM-01", "佐藤 賢太", "PM", ["Project Management", "Agile", "FastAPI", "Python"], 110),
            EngineerProfile("ENG-TL-02", "山田 花子", "Tech Lead", ["TypeScript", "Next.js", "React", "Node.js", "AWS"], 95),
            EngineerProfile("ENG-DEV-03", "田中 太郎", "Senior Dev", ["Go", "Kubernetes", "Docker", "GCP", "PostgreSQL"], 85),
            EngineerProfile("ENG-DEV-04", "鈴木 一郎", "Senior Dev", ["Python", "FastAPI", "PyTorch", "LangChain"], 85),
            EngineerProfile("ENG-QA-05", "高橋 次郎", "QA", ["Playwright", "Jest", "CI/CD", "Selenium"], 65),
        ]

    def compose_team(
        self,
        project_title: str,
        required_roles: List[str],
        required_skills: List[str],
        budget_max_man_yen: Optional[int] = None
    ) -> TeamCompositionResult:
        selected_members: List[EngineerProfile] = []
        covered_skills = set()

        for role in required_roles:
            candidates = [e for e in self.engineers if e.role == role and e not in selected_members]
            if candidates:
                # Rank candidates by skill overlap
                candidates.sort(
                    key=lambda c: sum(1 for s in c.skills if any(req.lower() in s.lower() for req in required_skills)),
                    reverse=True
                )
                chosen = candidates[0]
                selected_members.append(chosen)
                covered_skills.update([s.lower() for s in chosen.skills])
            else:
                # Fallback to general dev if specialized role not found
                fallback = [e for e in self.engineers if e not in selected_members]
                if fallback:
                    selected_members.append(fallback[0])

        total_rate = sum(m.monthly_rate for m in selected_members)
        req_skills_lower = [s.lower() for s in required_skills]
        coverage_count = sum(1 for req in req_skills_lower if any(req in cov for cov in covered_skills))
        skill_coverage = (coverage_count / len(required_skills)) * 100 if required_skills else 95.0

        # Synergy bonus for multi-role balanced team
        role_diversity = len(set(m.role for m in selected_members))
        synergy_score = min(100.0, 75.0 + (role_diversity * 5.0))
        overall_fit = round((skill_coverage * 0.6) + (synergy_score * 0.4), 1)

        proposal_text = (
            f"【チーム一括ご提案】「{project_title}」向け即戦力開発チーム編成案\n"
            f"■ 編成規模: {len(selected_members)}名一括体制 / 月額目安: {total_rate}万円\n"
            f"■ 体制構成:\n"
            + "\n".join([f"  ・{m.role}: {m.name} (主要技術: {', '.join(m.skills[:3])})" for m in selected_members])
            + f"\n■ 適合度評価: 総合フィット度 {overall_fit}% (技術カバレッジ {skill_coverage:.1f}%)\n"
            f"PM主導による自走型スクラム開発体制により、オンボーディング工数を70%削減いたします。"
        )

        return TeamCompositionResult(
            team_name=f"{project_title} 専任開発チームパック",
            members=selected_members,
            total_monthly_rate=total_rate,
            skill_coverage_score=round(skill_coverage, 1),
            synergy_score=round(synergy_score, 1),
            overall_fit_score=overall_fit,
            recommended_proposal_text=proposal_text,
        )
