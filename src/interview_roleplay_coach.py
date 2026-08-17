#!/usr/bin/env python3
"""Interview Roleplay Coach & Rehearsal Simulator Module (T984 - Action 21).

Generates project-tailored technical & behavioral interview questions, model answers,
and evaluates engineer practice responses to maximize interview pass rates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class InterviewPrepPackage:
    project_title: str
    target_skills: List[str]
    technical_questions: List[Dict[str, str]]
    behavioral_questions: List[Dict[str, str]]
    killer_reverse_questions: List[str]
    coaching_advice: str


@dataclass
class AnswerEvaluationResult:
    question: str
    engineer_answer: str
    score: int  # 1 - 100
    strengths: List[str]
    areas_for_improvement: List[str]
    recommended_model_answer: str


class InterviewRoleplayCoach:
    def __init__(self) -> None:
        pass

    def generate_prep_package(self, project_title: str, required_skills: List[str]) -> InterviewPrepPackage:
        tech_q = [
            {
                "question": f"{required_skills[0]}の実務において直面した最も困難なパフォーマンス/設計課題と、それをどう解決したか教えてください。",
                "intent": "実務経験の深さと自律的な問題解決能力の確認",
                "ideal_answer_points": "課題の背景・具体的なアプローチ手法・定量的成果（レイテンシ削減率やスループット向上）"
            },
            {
                "question": "チーム開発でのコードレビューや設計方針の不一致が発生した際、どのように合意形成を図りますか？",
                "intent": "コミュニケーション能力とチームシナジーの確認",
                "ideal_answer_points": "客観的なデータや標準規約に基づいた建設的な対話姿勢"
            }
        ]

        behavioral_q = [
            {
                "question": "リモート環境下でキャッチアップを円滑に進めるために工夫していることを教えてください。",
                "intent": "自走力と自発的なコミュニケーション姿勢の確認",
                "ideal_answer_points": "ドキュメント確認、Slack等での適時質問、タスク進捗の早期可視化"
            }
        ]

        reverse_q = [
            "現在チームで直近最も注力されている技術的チャレンジは何でしょうか？",
            "本ポジションのメンバーが参画後、最初の1ヶ月で達成することを期待される成果は何ですか？",
            "リリース頻度やCI/CDの運用フローについて教えていただけますでしょうか。"
        ]

        advice = (
            f"「{project_title}」の面談では、単なる構文理解だけでなく、{', '.join(required_skills[:2])}を用いた"
            f"アーキテクチャ設計・運用保守の実践的な工夫をエピソードを交えて語ることが合格の鍵となります。"
        )

        return InterviewPrepPackage(
            project_title=project_title,
            target_skills=required_skills,
            technical_questions=tech_q,
            behavioral_questions=behavioral_q,
            killer_reverse_questions=reverse_q,
            coaching_advice=advice
        )

    def evaluate_engineer_answer(self, question: str, engineer_answer: str) -> AnswerEvaluationResult:
        ans_len = len(engineer_answer)
        score = 70

        strengths = []
        improvements = []

        if ans_len >= 50:
            score += 15
            strengths.append("十分な情報量で具体的に回答できています。")
        else:
            improvements.append("回答がやや簡潔すぎるため、具体的なエピソードや数字を追加してください。")

        if "経験" in engineer_answer or "実装" in engineer_answer or "改善" in engineer_answer:
            score += 10
            strengths.append("実務経験に基づいたアクションが明確に伝わります。")
        else:
            improvements.append("「何を担当しどう工夫したか」の実績キーワードを盛り込むと説得力が増します。")

        score = min(100, max(40, score))

        model_ans = (
            f"「前職のプロジェクトでは、{question[:20]}... という課題に対し、"
            f"ボトルネックのプロファイリングを実施した上で設計見直しを行い、処理速度を30%向上させました。」"
        )

        return AnswerEvaluationResult(
            question=question,
            engineer_answer=engineer_answer,
            score=score,
            strengths=strengths,
            areas_for_improvement=improvements,
            recommended_model_answer=model_ans
        )
