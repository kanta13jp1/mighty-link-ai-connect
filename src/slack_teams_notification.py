"""Slack / Teams Webhook notification module for high-score matching & daily digest (T961)."""

import json
import logging
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


def _require_https_webhook_url(webhook_url: str) -> str:
    normalized = webhook_url.strip()
    parts = urlsplit(normalized)
    if (
        parts.scheme.lower() != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
    ):
        raise ValueError("Webhook URL must be HTTPS and must not embed credentials")
    return normalized


def build_slack_instant_card(
    job_title: str,
    engineer_name: str,
    score: float,
    reason: str,
    dashboard_url: str = "https://mightylink-app.com/#matching-section"
) -> Dict[str, Any]:
    """Build a Slack Block Kit payload for high-matching instant alert (score >= 80%)."""
    emoji = "🔥" if score >= 90 else "✨"
    return {
        "text": f"{emoji} 【高マッチ速報】適合度 {score:.1f}% の案件・人材が検出されました！",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 高マッチング速報 (適合度: {score:.1f}%)",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*案件名:*\n{job_title}"},
                    {"type": "mrkdwn", "text": f"*候補人材:*\n{engineer_name}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI適合理由:*\n{reason}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "詳細・提案レビューを開く"},
                        "url": dashboard_url,
                        "style": "primary"
                    }
                ]
            }
        ]
    }

def build_slack_daily_digest(
    date_str: str,
    total_emails: int,
    high_match_count: int,
    top_matches: List[Dict[str, Any]],
    dashboard_url: str = "https://mightylink-app.com/#matching-section"
) -> Dict[str, Any]:
    """Build a Slack Block Kit payload for 09:00 AM daily digest."""
    fields = [
        {"type": "mrkdwn", "text": f"*取込総メール数:*\n{total_emails} 件"},
        {"type": "mrkdwn", "text": f"*高マッチ(80%以上):*\n{high_match_count} 件"}
    ]
    
    top_summary = ""
    for idx, match in enumerate(top_matches[:3], 1):
        top_summary += f"{idx}. *{match.get('job_title', '案件')}* × *{match.get('engineer_name', '人材')}* ({match.get('score', 0):.0f}%)\n"
    
    if not top_summary:
        top_summary = "本日の高スコア案件はありません。"

    return {
        "text": f"📊 【日次サマリ】{date_str} 営業メールAIマッチング集計 (取込: {total_emails}件 / 高マッチ: {high_match_count}件)",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 営業メールAI 日次ダイジェスト ({date_str})",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": fields
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔥 本日の上位ベストマッチ:*\n{top_summary}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "管理ダッシュボードで確認"},
                        "url": dashboard_url
                    }
                ]
            }
        ]
    }

def send_webhook_notification(webhook_url: Optional[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send payload to Webhook URL. If URL is None/empty, return dry-run response safely."""
    if not webhook_url or not webhook_url.strip():
        logger.info("Webhook URL not configured. Operating in dry-run mode.")
        return {"status": "dry_run", "sent": False, "payload": payload}

    data = json.dumps(payload).encode("utf-8")
    try:
        safe_webhook_url = _require_https_webhook_url(webhook_url)
        req = urllib.request.Request(
            safe_webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 -- webhook is validated HTTPS.
            status_code = resp.getcode()
            return {"status": "success", "sent": True, "status_code": status_code}
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")
        return {"status": "error", "sent": False, "error": str(e)}
