"""AI Feedback Flywheel & Dynamic Prompt Tuning Module (T962)."""

from typing import Any, Dict, List, Optional

def aggregate_feedback_logs(feedback_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate recent feedback records to extract positive & negative patterns."""
    accepted_cases = []
    rejected_reasons = []
    preferred_skills = {}

    for record in feedback_records:
        action = record.get("action")  # 'accept' or 'reject'
        reason = record.get("reason", "")
        skills = record.get("skills", [])
        
        if action == "accept":
            accepted_cases.append({
                "job_title": record.get("job_title", ""),
                "engineer_name": record.get("engineer_name", ""),
                "positive_factor": reason or "スキル・条件が合致"
            })
            for s in skills:
                preferred_skills[s] = preferred_skills.get(s, 0) + 1
        elif action == "reject":
            if reason:
                rejected_reasons.append(reason)

    return {
        "total_feedback_count": len(feedback_records),
        "accepted_count": len(accepted_cases),
        "rejected_count": len(rejected_reasons),
        "preferred_skills": preferred_skills,
        "recent_accepted_examples": accepted_cases[:3],
        "top_rejected_reasons": rejected_reasons[:5]
    }

def generate_tuning_context(aggregated_data: Dict[str, Any]) -> str:
    """Generate dynamic prompt context to inject into LLM matching prompt."""
    if aggregated_data.get("total_feedback_count", 0) == 0:
        return "【過去フィードバック学習】蓄積されたフィードバックはまだありません。標準基準で判定します。"

    lines = [
        "【自社特化型AI学習フィードバック（過去の成約・見送り傾向）】",
        f"- 過去蓄積サンプル数: {aggregated_data['total_feedback_count']} 件 (採用: {aggregated_data['accepted_count']}件, 見送り: {aggregated_data['rejected_count']}件)"
    ]

    if aggregated_data.get("preferred_skills"):
        top_skills = sorted(aggregated_data["preferred_skills"].items(), key=lambda x: x[1], reverse=True)[:3]
        skill_str = ", ".join([f"{k}({v}回成約)" for k, v in top_skills])
        lines.append(f"- 現場で成約実績の高い重点スキル: {skill_str}")

    if aggregated_data.get("top_rejected_reasons"):
        reasons_str = "; ".join(aggregated_data["top_rejected_reasons"][:3])
        lines.append(f"- 過去に見送られた主因（NG判定の参考にすること）: {reasons_str}")

    lines.append("※ 上記の現場実績傾向を考慮し、類似条件の案件・人材のマッチ度スコアを適切に最適化してください。")
    return "\n".join(lines)
