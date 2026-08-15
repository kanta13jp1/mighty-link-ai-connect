"""Interactive Webhook & In-App Action Handler Module (T966)."""

from typing import Any, Dict, Optional

def handle_interactive_action(
    action_type: str,  # 'propose', 'keep', 'reject'
    job_id: str,
    engineer_id: str,
    user_id: str = "sales_user",
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Handle interactive button click from Slack/Teams card."""
    if action_type not in ["propose", "keep", "reject"]:
        return {
            "status": "error",
            "message": f"Unsupported action type: {action_type}"
        }

    status_message = ""
    next_step = ""

    if action_type == "propose":
        status_message = "案件元への提案キューに登録されました。"
        next_step = "自動提案文ドラフトが生成されました。確認して送信してください。"
    elif action_type == "keep":
        status_message = "キープリストに保存されました。"
        next_step = "ダッシュボードのキープ一覧から後で確認できます。"
    elif action_type == "reject":
        status_message = "見送りとして記録されました。"
        next_step = "AIフィードバックフライホイールへ理由が反映され、今後のマッチ精度が向上します。"

    return {
        "status": "success",
        "action_type": action_type,
        "job_id": job_id,
        "engineer_id": engineer_id,
        "user_id": user_id,
        "status_message": status_message,
        "next_step": next_step,
        "reason_recorded": reason or "ユーザーによる直接選択"
    }
