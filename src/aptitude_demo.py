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

# --------------------------------------------------------------------------- #
# Score bands (T909, 2026-07-22 社長定例決定事項(1))
#
# A bare score ("54.3点") tells an employee nothing. These bands are the single
# source of truth for what counts as 正常 / 注意 / 面談目安: evaluate_responses(),
# the /api/aptitude-demo/legend endpoint and the UI legend all read this table,
# so the legend can never disagree with the band a person is actually shown.
#
# Ranges are on the 0-100 condition index and are contiguous to one decimal
# place (indices are rounded to 0.1). They correspond to the 1-5 averages
# 4.0 -> 75.0 and 3.0 -> 50.0.
#
# These are conversation prompts for self-care, NOT clinical cut-offs.
# --------------------------------------------------------------------------- #
SCORE_BANDS: list[dict[str, Any]] = [
    {
        "id": "watch",
        "label": "面談目安",
        "min_index": 0.0,
        "max_index": 49.9,
        "guidance": "負荷が高まっている可能性があります。早めに話を聴く機会を設けることを推奨します。",
        "follow_up": "今月中に1対1で状況を確認し、必要に応じて業務量の調整や相談窓口の案内を検討します。",
    },
    {
        "id": "moderate",
        "label": "注意",
        "min_index": 50.0,
        "max_index": 74.9,
        "guidance": "おおむね安定していますが、気になる項目があれば早めに共有しておきたい状態です。",
        "follow_up": "次回の定例フィードバック面談で、低い項目を中心に様子を確認します。",
    },
    {
        "id": "good",
        "label": "正常",
        "min_index": 75.0,
        "max_index": 100.0,
        "guidance": "全体として前向きなコンディションがうかがえます。",
        "follow_up": "現在の良い習慣を継続し、通常どおり月次の面談で状況を確認します。",
    },
]

# Talking points per band for the monthly 10-20 minute feedback conversation.
_BAND_TALKING_POINTS: dict[str, list[str]] = {
    "good": [
        "最近うまくいっていること、続けたいことはありますか。",
        "今の進め方で負担に感じている部分はありませんか。",
        "次の1か月で挑戦したいことがあれば教えてください。",
    ],
    "moderate": [
        "この1か月で、特に気力を使った場面はどこでしたか。",
        "業務量やスケジュールで調整できると助かる点はありますか。",
        "休憩や切り替えの時間は取れていますか。",
    ],
    "watch": [
        "最近、負担が大きいと感じている業務はどれですか。",
        "手放せる作業や、分担できる作業はありますか。",
        "休息はとれていますか。生活リズムで気になることはありますか。",
        "会社として今すぐ手当てできることはありますか。",
    ],
}

# Extra prompt keyed off the weakest dimension, so the conversation starts from
# what the person actually reported rather than from the aggregate number.
_DIMENSION_PROMPT: dict[str, str] = {
    "energy": "エネルギー面のスコアが相対的に低めでした。1日の中で消耗しやすい時間帯はありますか。",
    "focus": "集中に関する項目が相対的に低めでした。集中が途切れやすい要因に心当たりはありますか。",
    "workload": "業務量の項目が相対的に低めでした。今の担当量は現実的だと感じますか。",
    "sleep": "休息に関する項目が相対的に低めでした。睡眠や休憩の確保で困っていることはありますか。",
    "team": "チーム連携の項目が相対的に低めでした。相談しやすさや情報共有で気になる点はありますか。",
}

INTERVIEW_CAUTION = (
    "本スコアはセルフチェックの目安であり、人事評価・処遇判断の材料には使用しません。"
    "医療的な判断も行いません。会話のきっかけとしてご利用ください。"
)

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


_REFLECTION: dict[str, str] = {
    "good": "全体として前向きなコンディションがうかがえます。良い習慣を続けましょう。",
    "moderate": "おおむね安定していますが、休息や相談の機会を意識するとより良いでしょう。",
    "watch": "負荷が高まっている可能性があります。休息の確保や、信頼できる人・窓口への相談を検討してください。",
}


def band_for_index(condition_index: float) -> dict[str, Any]:
    """The score band a 0-100 condition index falls into.

    Out-of-range values are clamped rather than raising: this drives a UI label,
    and refusing to render a band is worse than showing the nearest one.
    """
    try:
        index = float(condition_index)
    except (TypeError, ValueError):
        index = 0.0
    index = max(0.0, min(100.0, index))
    for band in SCORE_BANDS:
        if band["min_index"] <= index <= band["max_index"]:
            return band
    return SCORE_BANDS[-1]


def score_legend() -> dict[str, Any]:
    """Band table + scale for the UI legend (no evaluation involved)."""
    return {"score_bands": SCORE_BANDS, "scale": question_scale()}


def interview_guide(band_id: str, dimension_scores: dict[str, float]) -> dict[str, Any]:
    """Material for the monthly 10-20 minute feedback conversation (T909).

    Generic self-care prompts only — this is a conversation aid, never a
    diagnosis and never an input to a personnel evaluation.
    """
    band = next((b for b in SCORE_BANDS if b["id"] == band_id), SCORE_BANDS[-1])
    points = list(_BAND_TALKING_POINTS.get(band["id"], []))

    focus_dimension = None
    if dimension_scores:
        focus_dimension = min(dimension_scores, key=lambda d: dimension_scores[d])
        prompt = _DIMENSION_PROMPT.get(focus_dimension)
        if prompt:
            points.insert(0, prompt)

    return {
        "band": band["id"],
        "band_label": band["label"],
        "suggested_minutes": "10〜20分",
        "opening": "今月のセルフチェックの結果を一緒に見ながら、話せる範囲で聞かせてください。",
        "focus_dimension": focus_dimension,
        "talking_points": points,
        "follow_up": band["follow_up"],
        "caution": INTERVIEW_CAUTION,
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

    # The band comes from the shared table so the legend the employee reads and
    # the judgement they are shown can never drift apart (T909).
    band = band_for_index(condition_index)
    reflection = _REFLECTION[band["id"]]

    return {
        "answered_count": len(valid),
        "dimension_scores": dimension_scores,
        "overall_score": overall,
        "condition_index": condition_index,
        "band": band["id"],
        "band_label": band["label"],
        "band_range": [band["min_index"], band["max_index"]],
        "score_bands": SCORE_BANDS,
        "reflection": reflection,
        "interview_guide": interview_guide(band["id"], dimension_scores),
        "disclaimer": "本結果は医療的診断ではありません。継続的な不調がある場合は専門家にご相談ください。",
        "privacy_notice": PRIVACY_NOTICE,
        "persisted": False,
    }
