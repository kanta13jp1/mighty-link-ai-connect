"""Client Credibility & Contract Chain Depth Scorer Module (T970)."""

import re
from typing import Any, Dict, List, Optional

def analyze_client_credibility(email_body_or_text: str) -> Dict[str, Any]:
    """Analyze contract chain depth (direct/prime/sub) and payment terms from email context."""
    text = email_body_or_text.lower()
    
    # 1. Commercial Chain Depth Analysis
    chain_type = "2次請け・一般SES"
    chain_score = 75.0
    risk_flags = []

    if "エンド直" in text or "直請" in text or "プライム直" in text or "自社開発" in text:
        chain_type = "エンド直 / 自社プロダクト"
        chain_score = 100.0
    elif "元請" in text or "プライム" in text or "1次請" in text:
        chain_type = "元請け / 1次請け"
        chain_score = 90.0
    elif "多重" in text or "3次" in text or "4次" in text or "再委託" in text:
        chain_type = "多重下請け（注意）"
        chain_score = 45.0
        risk_flags.append("商流が深く（3次請け以降）、中間マージンや意思決定遅延のリスクがあります。")

    # 2. Payment Term Analysis
    payment_terms = "月末締め翌月末払い（30日サイト）"
    payment_score = 90.0

    if "翌々月" in text or "60日" in text:
        payment_terms = "月末締め翌々月末払い（60日サイト）"
        payment_score = 60.0
        risk_flags.append("支払いサイトが60日と長く、資金繰りキャッシュフローに注意が必要です。")
    elif "翌月20日" in text or "翌月15日" in text or "20日" in text:
        payment_terms = "短納期支払い（20日サイト以内）"
        payment_score = 100.0

    # Composite Credibility Index (0 to 100)
    composite_credibility = (chain_score * 0.6) + (payment_score * 0.4)

    rating = "A"
    if composite_credibility >= 90:
        rating = "AAA (優良・エンド直案件)"
    elif composite_credibility >= 80:
        rating = "AA (健全・プライム案件)"
    elif composite_credibility >= 65:
        rating = "A (標準的SES商流)"
    else:
        rating = "B (要確認・リスクあり)"

    return {
        "status": "success",
        "credibility_score": round(composite_credibility, 1),
        "credibility_rating": rating,
        "chain_depth_type": chain_type,
        "chain_score": chain_score,
        "payment_terms": payment_terms,
        "payment_score": payment_score,
        "risk_flags": risk_flags,
        "is_safe_to_propose": composite_credibility >= 60.0
    }
