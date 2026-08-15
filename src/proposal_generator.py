"""Proposal & Inquiry Draft Generator Module for Client and Engineer (T964)."""

from typing import Any, Dict, Optional

def generate_client_proposal_draft(
    job_title: str,
    client_company_name: str,
    engineer_name: str,
    experience_summary: str,
    rate_monthly_man_yen: int,
    available_date: str,
    sales_rep_name: str = "営業担当"
) -> Dict[str, str]:
    """Generate a ready-to-send proposal email draft for client company."""
    subject = f"【要員ご提案】{job_title} 向けのご提案（{engineer_name}様 / {available_date}稼働可）"
    body = f"""{client_company_name}
ご担当者様

いつも大変お世話になっております。
株式会社MightyLINKの{sales_rep_name}です。

ご提示いただいております案件「{job_title}」につきまして、
非常にマッチ度の高い弊社おすすめのエンジニア（{engineer_name}様）をご提案いたします。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 候補エンジニア概要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
・氏名（イニシャル）: {engineer_name}
・稼働開始可能日: {available_date}
・ご提案単価: {rate_monthly_man_yen}万円/月（税別・精算幅相談可）
・スキル・経験要約:
{experience_summary}

■ おすすめポイント
本案件で求められている必須要件に十分な実務経験を有しており、
即戦力として開発に貢献可能です。

詳細なスキルシートをご用意しておりますので、
面談のご調整や追加のご質問がございましたらお気軽にお申し付けください。

何卒よろしくお願い申し上げます。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return {
        "subject": subject,
        "body": body.strip(),
        "type": "client_proposal"
    }

def generate_engineer_inquiry_draft(
    job_title: str,
    engineer_name: str,
    project_overview: str,
    rate_monthly_man_yen: int,
    location_and_remote: str,
    coordinator_name: str = "コーディネーター"
) -> Dict[str, str]:
    """Generate a friendly project inquiry draft for candidate engineer."""
    subject = f"【案件のご紹介】{job_title} の打診（{engineer_name}様）"
    body = f"""{engineer_name}様

お疲れ様です！MightyLINKの{coordinator_name}です。

{engineer_name}様のご経験・ご希望にフィットするおすすめの新規案件が参りましたので、
ぜひご紹介させていただきたくご連絡いたしました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 案件概要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【案件名】{job_title}
【想定単価】〜{rate_monthly_man_yen}万円/月
【勤務形態】{location_and_remote}
【業務内容・魅力】
{project_overview}

【おすすめ理由】
{engineer_name}様の得意とされるスキルが直接活かせる環境で、
働き方や技術スタックの相性も非常に良好と判断しております。

もしご興味をお持ちいただけましたら、詳細な条件やクライアント情報をお伝えしますので、
お気軽にご返信いただけますと幸いです！

どうぞよろしくお願いいたします。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return {
        "subject": subject,
        "body": body.strip(),
        "type": "engineer_inquiry"
    }
