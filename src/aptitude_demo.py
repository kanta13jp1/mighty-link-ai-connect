"""Session-only aptitude / motivation self-check demo (T876).

CEO 2026-07-08 request: dynamically generate ~10-20 questions that give an
employee a light read on their motivation / condition, evaluate on-screen only.

Legal constraint (R119 / QA-105): the answers and any derived "mental-state"
score are 要配慮個人情報 (special-care personal information). This prototype must
NEVER persist them. That guarantee is made structural here: this module does not
import any database, Supabase, SQLite, or storage helper — it is pure in-memory
logic, so there is no code path that could write a response to storage. The API
layer (src/app.py) only calls these pure functions and returns the result.

Design safety:
* Questions probe *indirect* well-being indicators (energy, focus, workload
  balance, sleep quality, team connection) on a 1-5 scale. They never ask for a
  diagnosis, medication, self-harm, or a named condition.
* AI-generated questions pass a sensitive-term filter; anything asking directly
  about 要配慮 topics is dropped and back-filled from the vetted fallback set.
* Evaluation returns a general self-care reflection, explicitly NOT a medical
  diagnosis.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional


QUESTION_MIN = 10
QUESTION_MAX = 20
QUESTION_DEFAULT = 12
SCALE_MIN = 1
SCALE_MAX = 5

PRIVACY_NOTICE = (
    "この診断は体験用プロトタイプです。回答および結果はサーバーやデータベースに"
    "一切保存されず、この画面のセッション内でのみ評価されます（要配慮個人情報の"
    "蓄積を行いません）。本結果は医療的診断ではなく、セルフケアのための一般的な"
    "気づきを目的としています。"
)

# Vetted fallback questions — indirect well-being indicators, never a diagnosis.
# Each has a dimension so evaluation can group scores without storing anything.
FALLBACK_QUESTIONS: list[dict[str, str]] = [
    {"id": "q_energy_1", "dimension": "energy", "text": "最近1週間、仕事に取り組むエネルギーが十分にあると感じましたか。"},
    {"id": "q_energy_2", "dimension": "energy", "text": "朝、仕事を始めるときに前向きな気持ちで臨めていますか。"},
    {"id": "q_focus_1", "dimension": "focus", "text": "業務に集中して取り組めている時間が多いと感じますか。"},
    {"id": "q_focus_2", "dimension": "focus", "text": "やるべきことの優先順位を落ち着いて整理できていますか。"},
    {"id": "q_workload_1", "dimension": "workload", "text": "現在の業務量は無理なくこなせる範囲だと感じますか。"},
    {"id": "q_workload_2", "dimension": "workload", "text": "休憩や区切りを取りながら働けていますか。"},
    {"id": "q_sleep_1", "dimension": "recovery", "text": "睡眠や休息で十分に回復できていると感じますか。"},
    {"id": "q_sleep_2", "dimension": "recovery", "text": "仕事から離れてリフレッシュする時間を確保できていますか。"},
    {"id": "q_team_1", "dimension": "connection", "text": "困ったときに周囲へ相談しやすい環境だと感じますか。"},
    {"id": "q_team_2", "dimension": "connection", "text": "チームの中で自分の意見を伝えやすいと感じますか。"},
    {"id": "q_growth_1", "dimension": "motivation", "text": "今の仕事にやりがいや成長を感じられていますか。"},
    {"id": "q_growth_2", "dimension": "motivation", "text": "今後の目標に向けて前向きに取り組めていますか。"},
    {"id": "q_balance_1", "dimension": "workload", "text": "仕事とプライベートのバランスが取れていると感じますか。"},
    {"id": "q_focus_3", "dimension": "focus", "text": "落ち着いて物事を判断できる状態だと感じますか。"},
    {"id": "q_energy_3", "dimension": "energy", "text": "一日を通して気力を保てていると感じますか。"},
    {"id": "q_connection_3", "dimension": "connection", "text": "職場で孤立せず、つながりを感じられていますか。"},
    {"id": "q_recovery_3", "dimension": "recovery", "text": "週末や休暇で気持ちを切り替えられていますか。"},
    {"id": "q_motivation_3", "dimension": "motivation", "text": "自分の仕事が誰かの役に立っていると実感できますか。"},
    {"id": "q_workload_3", "dimension": "workload", "text": "締め切りや納期に過度なプレッシャーを感じずに済んでいますか。"},
    {"id": "q_focus_4", "dimension": "focus", "text": "新しいことに前向きに取り組む余裕がありますか。"},
]
# The vetted set must cover the maximum request size so any 10-20 count is
# satisfiable from fallback alone (T876 legal safety net).
assert len(FALLBACK_QUESTIONS) >= QUESTION_MAX

# Terms that would turn an indirect check into a direct 要配慮 medical probe.
# A generated question containing any of these is rejected.
SENSITIVE_DIRECT_PATTERNS = [
    "うつ", "鬱", "診断", "病名", "疾患", "精神疾患", "障害", "自殺", "自傷",
    "希死", "服薬", "薬を", "通院", "入院", "カウンセリング", "セラピー",
    "既往", "持病", "メンタルヘルス不調", "休職", "労災", "ハラスメント",
]

_SCALE_LABEL = {
    1: "とてもそう思わない",
    2: "あまりそう思わない",
    3: "どちらともいえない",
    4: "ややそう思う",
    5: "とてもそう思う",
}


def question_scale() -> dict[str, Any]:
    return {"min": SCALE_MIN, "max": SCALE_MAX, "labels": dict(_SCALE_LABEL)}


def is_safe_question(text: str) -> bool:
    """True if the question does not directly probe a 要配慮 medical topic."""
    if not text or not text.strip():
        return False
    return not any(term in text for term in SENSITIVE_DIRECT_PATTERNS)


def clamp_count(count: Optional[int]) -> int:
    if not isinstance(count, int):
        return QUESTION_DEFAULT
    return max(QUESTION_MIN, min(QUESTION_MAX, count))


def build_generation_prompt(count: int) -> str:
    return (
        f"あなたは従業員のセルフケアを支援するアシスタントです。以下の条件で、"
        f"仕事のモチベーションとコンディションを本人が振り返るための質問を{count}問、"
        "日本語で作成してください。\n"
        "条件:\n"
        "- 5段階（1:とてもそう思わない〜5:とてもそう思う）で答えられる肯定文にする。\n"
        "- エネルギー/集中/業務量/回復・休息/対人関係/やりがい 等の間接的な指標を扱う。\n"
        "- 病名・診断・服薬・通院・自傷・休職など医療的/要配慮個人情報を直接尋ねない。\n"
        "- 各質問はJSON配列の要素 {\"dimension\": <領域>, \"text\": <質問文>} とする。\n"
        "JSON配列のみを出力してください。"
    )


def _coerce_generated(raw: Any) -> list[dict[str, str]]:
    import json

    if isinstance(raw, str):
        text = raw.strip()
        # tolerate ```json fences
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        data = json.loads(text)
    else:
        data = raw
    items = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("generated questions payload is not a list")
    out: list[dict[str, str]] = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            out.append({"dimension": "general", "text": item.strip()})
        elif isinstance(item, dict) and item.get("text"):
            out.append({"dimension": str(item.get("dimension") or "general"),
                        "text": str(item["text"]).strip()})
    return out


def sanitize_questions(questions: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    """Keep only safe questions, dedupe, and back-fill from the vetted set."""
    safe: list[dict[str, str]] = []
    seen: set[str] = set()
    for q in questions:
        text = (q.get("text") or "").strip()
        if not is_safe_question(text) or text in seen:
            continue
        seen.add(text)
        safe.append({"id": q.get("id") or f"q_gen_{len(safe) + 1}",
                     "dimension": q.get("dimension") or "general", "text": text})
        if len(safe) >= count:
            break
    for fb in FALLBACK_QUESTIONS:
        if len(safe) >= count:
            break
        if fb["text"] in seen:
            continue
        seen.add(fb["text"])
        safe.append(dict(fb))
    return safe[:count]


def generate_questions(
    count: Optional[int] = None,
    gemini_caller: Optional[Callable[[str], Any]] = None,
) -> dict[str, Any]:
    """Return a session-only question set. Never persists anything.

    gemini_caller, when provided, is a function(prompt:str)->raw text/obj. Any
    failure falls back to the vetted question set so the demo always works.
    """
    n = clamp_count(count)
    source = "fallback"
    generated: list[dict[str, str]] = []
    if gemini_caller is not None:
        try:
            raw = gemini_caller(build_generation_prompt(n))
            generated = _coerce_generated(raw)
            if generated:
                source = "ai_generated"
        except Exception:
            generated = []
            source = "fallback"
    questions = sanitize_questions(generated, n)
    return {
        "questions": questions,
        "count": len(questions),
        "source": source,
        "scale": question_scale(),
        "privacy_notice": PRIVACY_NOTICE,
        "persisted": False,
    }


def evaluate_responses(answers: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate 1-5 answers on-screen only. Never persists anything.

    answers: [{"dimension": str, "value": int}, ...]. Returns dimension averages,
    an overall condition index, and a general (non-medical) reflection.
    """
    valid = []
    for a in answers or []:
        try:
            value = int(a.get("value"))
        except (TypeError, ValueError):
            continue
        if SCALE_MIN <= value <= SCALE_MAX:
            valid.append({"dimension": str(a.get("dimension") or "general"), "value": value})
    if not valid:
        raise ValueError("at least one valid 1-5 answer is required")

    by_dim: dict[str, list[int]] = {}
    for a in valid:
        by_dim.setdefault(a["dimension"], []).append(a["value"])
    dimension_scores = {
        dim: round(sum(vals) / len(vals), 2) for dim, vals in sorted(by_dim.items())
    }
    overall = round(sum(a["value"] for a in valid) / len(valid), 2)
    # 1-5 scale -> 0-100 condition index for display only
    condition_index = round((overall - SCALE_MIN) / (SCALE_MAX - SCALE_MIN) * 100, 1)

    if overall >= 4.0:
        band, reflection = "good", "全体として前向きなコンディションがうかがえます。良い習慣を続けましょう。"
    elif overall >= 3.0:
        band, reflection = "moderate", "おおむね安定していますが、休息や相談の機会を意識するとより良いでしょう。"
    else:
        band, reflection = "watch", "負荷が高まっている可能性があります。休息の確保や、信頼できる人・窓口への相談を検討してください。"

    return {
        "answered_count": len(valid),
        "dimension_scores": dimension_scores,
        "overall_score": overall,
        "condition_index": condition_index,
        "band": band,
        "reflection": reflection,
        "disclaimer": "本結果は医療的診断ではありません。継続的な不調がある場合は専門家にご相談ください。",
        "privacy_notice": PRIVACY_NOTICE,
        "persisted": False,
    }
