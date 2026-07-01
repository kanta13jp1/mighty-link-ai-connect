"""AI and deterministic fallback parser for sales emails (T817_4)."""

from __future__ import annotations

import json
import os
import re
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types as genai_types

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"


def get_gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


# Pydantic models for structured JSON output from Gemini
class ProjectRequirementJSON(BaseModel):
    title: str = Field(description="案件名。明示されていない場合は件名などから推測")
    client_or_partner: Optional[str] = Field(None, description="クライアント名またはBPパートナー企業名")
    summary: str = Field(description="業務内容・プロジェクト概要")
    required_skills: List[str] = Field(default_factory=list, description="必須スキル（Java, AWS, SQL等）の一覧")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="尚可・歓迎スキルの一覧")
    rate_min: Optional[int] = Field(None, description="最小単価（月額、万円単位の整数値。例: 80万円なら80）")
    rate_max: Optional[int] = Field(None, description="最大単価（月額、万円単位の整数値。例: 100万円なら100）")
    rate_unit: Optional[str] = Field("jpy_month", description="単価単位（jpy_month）")
    location: Optional[str] = Field(None, description="勤務地（最寄り駅、都市名など。例: 渋谷, 新宿）")
    remote_type: Optional[str] = Field("unknown", description="リモート形式 ('onsite', 'hybrid', 'remote', 'unknown')")
    start_date_text: Optional[str] = Field(None, description="稼働開始時期（例: 即日, 7月〜）")
    duration_text: Optional[str] = Field(None, description="期間・契約期間（例: 長期, 3ヶ月）")
    commercial_flow: Optional[str] = Field(None, description="商流（例: 直、元請直、二次請け）")
    restrictions: Optional[str] = Field(None, description="年齢制限、外国籍制限などの制限条件")

class TalentProfileJSON(BaseModel):
    anonymized_talent_key: str = Field(description="要員の匿名化識別ID（例: Aさん, Initial-T, 30代Java技術者など）")
    summary: str = Field(description="要員の経歴や得意分野の概要")
    skills: List[str] = Field(default_factory=list, description="保有・得意スキルの一覧")
    experience_years: Optional[float] = Field(None, description="経験年数（数値）")
    desired_rate_min: Optional[int] = Field(None, description="希望最小単価（月額、万円単位の整数値。例: 60）")
    desired_rate_max: Optional[int] = Field(None, description="希望最大単価（月額、万円単位の整数値。例: 80）")
    desired_location: Optional[str] = Field(None, description="希望勤務地・エリア")
    remote_preference: Optional[str] = Field("unknown", description="希望リモート形式 ('onsite', 'hybrid', 'remote', 'unknown')")
    availability_text: Optional[str] = Field(None, description="稼働可能時期（例: 即日, 7月中旬）")

class EmailParseResultJSON(BaseModel):
    category: str = Field(description="メール種別 ('project' (案件紹介), 'talent' (要員提案), 'other')")
    project: Optional[ProjectRequirementJSON] = Field(None, description="案件紹介の場合に格納される案件データ")
    talent: Optional[TalentProfileJSON] = Field(None, description="要員提案の場合に格納される要員データ")
    confidence: float = Field(description="抽出信頼度 (0.0 から 1.0)")
    evidence_excerpt: Optional[str] = Field(None, description="メール本文から抽出した要件の根拠となる原文抜粋")


class SalesEmailParser:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = get_gemini_model_name()
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[!] Failed to initialize Gemini Client: {e}")

    def parse(self, subject: str, body: str) -> EmailParseResultJSON:
        """Parse sales email content using Gemini API, with a deterministic fallback."""
        if not self.client:
            print("[*] Running in deterministic fallback mode (No API Key).")
            return self.fallback_parse(subject, body)

        prompt = f"""以下のIT系SES営業メール（件名と本文抜粋）から、案件要件、または要員情報を抽出し、構造化されたJSONデータを生成してください。

件名: {subject}
本文:
{body}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EmailParseResultJSON,
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return EmailParseResultJSON(**data)
        except Exception as e:
            print(f"[!] Gemini parsing failed: {e}. Falling back to deterministic parsing.")
            return self.fallback_parse(subject, body)

    def fallback_parse(self, subject: str, body: str) -> EmailParseResultJSON:
        """Deterministic keyword-based parsing fallback."""
        full_text = f"{subject}\n{body}"
        full_text_lower = full_text.lower()

        # 1. Determine Category
        category = "other"
        talent_keywords = [
            "\u8981\u54e1",  # 要員
            "\u6280\u8853\u8005",  # 技術者
            "\u8981\u54e1\u60c5\u5831",  # 要員情報
            "\u30a8\u30f3\u30b8\u30cb\u30a2\u60c5\u5831",  # エンジニア情報
            "\u7a3c\u50cd\u53ef",  # 稼働可
            "\u30b9\u30ad\u30eb\u30b7\u30fc\u30c8",  # スキルシート
            "\u6240\u5c5e",  # 所属
            "\u5f0a\u793e\u30d7\u30ed\u30d1\u30fc"  # 弊社プロパー
        ]
        project_keywords = [
            "\u6848\u4ef6",  # 案件
            "\u6848\u4ef6\u60c5\u5831",  # 案件情報
            "\u8981\u4ef6",  # 要件
            "\u958b\u767a\u8981\u54e1\u52df\u96c6",  # 開発要員募集
            "\u6c42\u3080",  # 求む
            "\u30a8\u30f3\u30b8\u30cb\u30a2\u52df\u96c6",  # エンジニア募集
            "\u6025\u52df"  # 急募
        ]

        t_count = sum(1 for kw in talent_keywords if kw in full_text)
        p_count = sum(1 for kw in project_keywords if kw in full_text)

        if t_count > p_count and t_count > 0:
            category = "talent"
        elif p_count >= t_count and p_count > 0:
            category = "project"

        # 2. Skill Extraction
        skills_master = [
            "java", "python", "c#", "c++", "php", "ruby", "go", "typescript", "javascript",
            "sql", "oracle", "postgres", "mysql", "aws", "azure", "gcp", "docker", "kubernetes",
            "linux", "git", "react", "vue", "angular", "rails", "django", "spring", "unity",
            "salesforce", "abap", "sap"
        ]
        found_skills = []
        for skill in skills_master:
            # Match word boundary or prefix/suffix patterns
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, full_text_lower):
                # Standardize casing
                found_skills.append(skill.upper() if skill != "javascript" and skill != "typescript" else skill.capitalize())

        # 3. Rate/Cost Extraction (e.g. 80万, ~75万円, 70-90万)
        rate_min = None
        rate_max = None
        # Match digits followed by range wave/hyphen/dash, then digits, then "万" (\u4e07)
        rate_matches = re.findall(r"(\d+)[\u301c\uff5e\-\u30fc](\d+)\s*[\u4e07]", full_text)
        if rate_matches:
            try:
                rate_min = int(rate_matches[0][0])
                rate_max = int(rate_matches[0][1])
            except ValueError:
                pass
        else:
            single_match = re.search(r"(\d+)\s*[\u4e07]", full_text)
            if single_match:
                try:
                    rate_max = int(single_match.group(1))
                except ValueError:
                    pass

        # 4. Remote Preference
        remote_type = "unknown"
        if any(kw in full_text for kw in [
            "\u30d5\u30eb\u30ea\u30e2\u30fc\u30c8",  # フルリモート
            "\u5b8c\u5168\u30ea\u30e2\u30fc\u30c8"  # 完全リモート
        ]):
            remote_type = "remote"
        elif any(kw in full_text for kw in [
            "\u30ea\u30e2\u30fc\u30c8\u53ef",  # リモート可
            "\u4e00\u90e8\u30ea\u30e2\u30fc\u30c8",  # 一部リモート
            "\u30cf\u30a4\u30d6\u30ea\u30c3\u30c9",  # ハイブリッド
            "\u5728\u5b85"  # 在宅
        ]):
            remote_type = "hybrid"
        elif any(kw in full_text for kw in [
            "\u5e38\u99d4",  # 常駐
            "\u30aa\u30f3\u30b5\u30a4\u30c8",  # オンサイト
            "\u51fa\u793e"  # 出社
        ]):
            remote_type = "onsite"

        # 5. Location
        locations = [
            "\u6e0b\u8c37",  # 渋谷
            "\u65b0\u5bbf",  # 新宿
            "\u6771\u4eac",  # 東京
            "\u54c1\u5ddd",  # 品川
            "\u516d\u672c\u6728",  # 六本木
            "\u79cb\u8449\u539f",  # 秋葉原
            "\u6c60\u888b",  # 池袋
            "\u65b0\u6a4b",  # 新橋
            "\u6a2a\u6d5c",  # 横浜
            "\u5927\u962a",  # 大阪
            "\u540d\u53e4\u5c4b",  # 名古屋
            "\u798f\u5ca1"  # 福岡
        ]
        found_location = None
        for loc in locations:
            if loc in full_text:
                found_location = loc
                break

        # 6. Assemble Object
        project_data = None
        talent_data = None
        evidence = ""

        # Extract first 3 lines of body as evidence
        lines = [line.strip() for line in body.splitlines() if line.strip()][:3]
        evidence = " | ".join(lines)

        if category == "project":
            project_data = ProjectRequirementJSON(
                title=subject or "無題の案件",
                client_or_partner=None,
                summary=collapse_whitespace(body[:200]) if body else "",
                required_skills=found_skills,
                nice_to_have_skills=[],
                rate_min=rate_min,
                rate_max=rate_max,
                location=found_location,
                remote_type=remote_type,
                start_date_text="即日" if "\u5373\u65e5" in full_text else None,  # 即日
                duration_text="長期" if "\u9577\u671f" in full_text else None,  # 長期
                commercial_flow="不明"
            )
        elif category == "talent":
            talent_data = TalentProfileJSON(
                anonymized_talent_key=f"技術者（{found_skills[0]}等）" if found_skills else "匿名技術者",
                summary=collapse_whitespace(body[:200]) if body else "",
                skills=found_skills,
                experience_years=None,
                desired_rate_min=rate_min,
                desired_rate_max=rate_max,
                desired_location=found_location,
                remote_preference=remote_type,
                availability_text="即日" if "\u5373\u65e5" in full_text else None  # 即日
            )

        return EmailParseResultJSON(
            category=category,
            project=project_data,
            talent=talent_data,
            confidence=0.5,
            evidence_excerpt=evidence
        )


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
