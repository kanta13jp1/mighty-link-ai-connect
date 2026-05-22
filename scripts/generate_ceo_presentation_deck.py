#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate a CEO-facing PowerPoint deck from the NotebookLM slide outline.

NotebookLM CLI currently provides the outline and talking points as text. This
script turns that NotebookLM output plus the local evidence manifests into an
editable PPTX that can be shown in the 2026-06-02 CEO meeting.
"""

from __future__ import annotations

import datetime as dt
import json
import zipfile
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "exports" / "knowledge_flow"
PPTX_FILE = EXPORT_DIR / "mighty_skill_bridge_ceo_presentation_2026-06-02.pptx"
SUMMARY_FILE = EXPORT_DIR / "mighty_skill_bridge_ceo_presentation_2026-06-02.md"
MANIFEST_FILE = EXPORT_DIR / "mighty_skill_bridge_ceo_presentation_2026-06-02.json"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

COLORS = {
    "ink": RGBColor(25, 34, 45),
    "muted": RGBColor(91, 105, 120),
    "blue": RGBColor(26, 115, 232),
    "blue_dark": RGBColor(16, 72, 154),
    "sky": RGBColor(230, 242, 255),
    "green": RGBColor(20, 146, 96),
    "green_bg": RGBColor(226, 246, 238),
    "amber": RGBColor(190, 124, 0),
    "amber_bg": RGBColor(255, 244, 218),
    "red": RGBColor(188, 68, 60),
    "red_bg": RGBColor(255, 232, 229),
    "line": RGBColor(217, 224, 232),
    "panel": RGBColor(247, 250, 253),
    "white": RGBColor(255, 255, 255),
}

FONT = "Yu Gothic"


def jst_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: int = 18,
    color: RGBColor | None = None,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    margin: float = 0.06,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = valign
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    p = frame.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    font = run.font
    font.name = FONT
    font.size = Pt(size)
    font.bold = bold
    font.color.rgb = color or COLORS["ink"]
    return box


def add_bullets(slide, bullets: list[str], x: float, y: float, w: float, h: float, *, size: int = 18):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    frame.margin_top = Inches(0.03)
    frame.margin_bottom = Inches(0.03)
    for index, bullet in enumerate(bullets):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = bullet
        p.level = 0
        p.space_after = Pt(8)
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = COLORS["ink"]
    return box


def add_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: RGBColor,
    line: RGBColor | None = None,
    radius: bool = False,
):
    shape_type = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    shape.line.width = Pt(1)
    return shape


def add_chip(slide, label: str, x: float, y: float, w: float, *, fill: RGBColor, text: RGBColor):
    add_rect(slide, x, y, w, 0.38, fill=fill, line=fill, radius=True)
    add_text(slide, label, x + 0.08, y + 0.055, w - 0.16, 0.24, size=10, color=text, bold=True, align=PP_ALIGN.CENTER)


def add_footer(slide, slide_no: int, source_note: str):
    add_text(
        slide,
        f"{slide_no:02d} / 08   {source_note}",
        0.6,
        7.12,
        9.2,
        0.25,
        size=8,
        color=COLORS["muted"],
    )
    add_text(
        slide,
        "Mighty Skill-Bridge / CEO meeting prep",
        10.4,
        7.12,
        2.3,
        0.25,
        size=8,
        color=COLORS["muted"],
        align=PP_ALIGN.RIGHT,
    )


def add_header(slide, slide_no: int, kicker: str, title: str, source_note: str):
    add_rect(slide, 0, 0, 13.333, 0.14, fill=COLORS["blue"], line=COLORS["blue"])
    add_text(slide, kicker, 0.62, 0.36, 3.8, 0.25, size=9, color=COLORS["blue"], bold=True)
    add_text(slide, title, 0.58, 0.68, 11.8, 0.74, size=28, color=COLORS["ink"], bold=True)
    add_footer(slide, slide_no, source_note)


def add_evidence_panel(slide, items: list[str], y: float = 5.72):
    add_rect(slide, 0.58, y, 12.18, 1.18, fill=COLORS["panel"], line=COLORS["line"])
    add_text(slide, "見せる証跡", 0.82, y + 0.18, 1.4, 0.25, size=10, color=COLORS["blue"], bold=True)
    add_bullets(slide, items, 2.05, y + 0.14, 10.35, 0.86, size=11)


def add_metric_card(slide, x: float, y: float, label: str, value: str, note: str, fill: RGBColor):
    add_rect(slide, x, y, 3.55, 1.42, fill=fill, line=COLORS["line"])
    add_text(slide, value, x + 0.22, y + 0.16, 3.1, 0.46, size=24, color=COLORS["blue_dark"], bold=True)
    add_text(slide, label, x + 0.24, y + 0.7, 3.05, 0.28, size=12, color=COLORS["ink"], bold=True)
    add_text(slide, note, x + 0.24, y + 1.02, 3.05, 0.28, size=9, color=COLORS["muted"])


def add_option_card(slide, x: float, title: str, audience: str, value: str, first_step: str):
    add_rect(slide, x, 2.0, 3.75, 2.55, fill=COLORS["panel"], line=COLORS["line"])
    add_text(slide, title, x + 0.22, 2.2, 3.25, 0.32, size=15, color=COLORS["blue_dark"], bold=True)
    add_text(slide, "想定対象", x + 0.22, 2.72, 0.9, 0.23, size=9, color=COLORS["muted"], bold=True)
    add_text(slide, audience, x + 1.08, 2.69, 2.2, 0.3, size=11, color=COLORS["ink"])
    add_text(slide, "価値", x + 0.22, 3.22, 0.9, 0.23, size=9, color=COLORS["muted"], bold=True)
    add_text(slide, value, x + 1.08, 3.15, 2.35, 0.45, size=11, color=COLORS["ink"])
    add_text(slide, "初手", x + 0.22, 3.92, 0.9, 0.23, size=9, color=COLORS["muted"], bold=True)
    add_text(slide, first_step, x + 1.08, 3.86, 2.35, 0.45, size=11, color=COLORS["ink"])


def add_flow_box(slide, x: float, y: float, title: str, note: str, fill: RGBColor):
    add_rect(slide, x, y, 2.3, 1.0, fill=fill, line=COLORS["line"], radius=True)
    add_text(slide, title, x + 0.16, y + 0.18, 1.95, 0.24, size=13, color=COLORS["ink"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, note, x + 0.18, y + 0.52, 1.9, 0.25, size=8, color=COLORS["muted"], align=PP_ALIGN.CENTER)


def add_arrow(slide, x: float, y: float):
    add_text(slide, "→", x, y, 0.35, 0.4, size=20, color=COLORS["blue"], bold=True, align=PP_ALIGN.CENTER)


def build_slides(prs: Presentation, context: dict[str, Any]) -> None:
    blank = prs.slide_layouts[6]
    source_note = f"NotebookLM CLI outline / notebook {context['notebook_id']}"

    # 1
    slide = prs.slides.add_slide(blank)
    add_header(slide, 1, "6/2 CEO Decision Meeting", "本日決めたいこと", source_note)
    add_text(slide, "企画を決め打ちする場ではなく、次の開発の向きと優先順位を決める場です。", 0.72, 1.55, 11.7, 0.45, size=18, color=COLORS["muted"])
    add_metric_card(slide, 0.8, 2.35, "サービス方向性", "1", "A/B/Cのどれを最初に育てるか", COLORS["sky"])
    add_metric_card(slide, 4.85, 2.35, "公式化する連携", "4候補", "NotebookLM / Slack / Notion / Obsidian", COLORS["green_bg"])
    add_metric_card(slide, 8.9, 2.35, "打合せ後の反映", "即時", "WBS / Calendar / Issues / Docs", COLORS["amber_bg"])
    add_bullets(
        slide,
        [
            "公開URLで動くデモと、Google Workspace同期の到達点を確認する。",
            "NotebookLMが生成した論点を材料に、社長への質問を短く整理する。",
            "未決事項は未決のまま残し、6/2後にWBSへ差し替える受け皿を用意する。",
        ],
        0.92,
        4.35,
        11.25,
        0.92,
        size=16,
    )
    add_evidence_panel(slide, ["CEO slide outline: exports/knowledge_flow/notebooklm_ceo_slide_outline.md", "PPTX: exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx"])

    # 2
    slide = prs.slides.add_slide(blank)
    add_header(slide, 2, "Prototype Status", "現在の到達点と公開デモ", source_note)
    add_text(slide, "社長に見せる公開URLは、UIデグレを防ぐガードを通して維持します。", 0.72, 1.52, 11.7, 0.38, size=17, color=COLORS["muted"])
    add_metric_card(slide, 0.8, 2.12, "Public Demo Guard", "PASS", "公開URLのREADME fallbackを検知", COLORS["green_bg"])
    add_metric_card(slide, 4.85, 2.12, "AI fallback", "LIVE/MOCK", "Gemini quota中も停止しない構成", COLORS["sky"])
    add_metric_card(slide, 8.9, 2.12, "WBS sync", f"{context['wbs_total']} tasks", "Sheets / Calendarへ同期", COLORS["amber_bg"])
    add_bullets(
        slide,
        [
            "経歴書・案件票から4軸フィット診断へ進むUIを維持。",
            "Gemini制限中はdeterministic fallbackとCodexで開発を継続。",
            "公開URLは社長共有済みのため、push前後のPublic Demo Guardを必須化。",
        ],
        0.92,
        4.15,
        11.2,
        0.98,
        size=16,
    )
    add_evidence_panel(slide, ["Public URL: https://kanta13jp1.github.io/mighty-link-ai-connect/", "Guard script: scripts/verify_public_demo.py", "Quota-safe flow: docs/CODEX_CONTINUATION_NOTES.md"])

    # 3
    slide = prs.slides.add_slide(blank)
    add_header(slide, 3, "Google Workspace", "Google Workspaceで進捗が回る基盤", source_note)
    for x, title, note, fill in [
        (0.82, "Codex", "実装・文書・WBS更新", COLORS["sky"]),
        (3.26, "WBS.tsv", "日程と状態の主ソース", COLORS["panel"]),
        (5.7, "Google Sheets", "CATS型WBS / Summary", COLORS["green_bg"]),
        (8.14, "Calendar", "開発予定を同期", COLORS["amber_bg"]),
        (10.58, "Docs / Drive", "NotebookLM投入資料", COLORS["sky"]),
    ]:
        add_flow_box(slide, x, 2.2, title, note, fill)
    for x in [2.82, 5.26, 7.7, 10.14]:
        add_arrow(slide, x, 2.48)
    add_bullets(
        slide,
        [
            "OAuth実行アカウントは k-umezawa@ml-mightylink.com に固定。",
            "WBSはGoogle Sheetsへ、主要予定はCalendarへ同期。",
            "docs配下はGoogle Docs化し、NotebookLM sourceとして再利用。",
        ],
        1.0,
        4.08,
        10.9,
        0.92,
        size=16,
    )
    add_evidence_panel(slide, [f"Workspace account: {context['account']}", f"NotebookLM sources ready: {context['source_count']}", "Spreadsheet ID: 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"])

    # 4
    slide = prs.slides.add_slide(blank)
    add_header(slide, 4, "Knowledge Flow", "開発ナレッジ連携の実績とデモ", source_note)
    lanes = [
        ("NotebookLM", "22 source ready\nAgent Brief / CEO outline取得済み", COLORS["sky"], "完了"),
        ("Slack", "投稿案生成済み\nCLI/MCP送信ツールは未露出", COLORS["amber_bg"], "権限確認待ち"),
        ("Notion", "証跡ページ作成\n意思決定DB候補を管理", COLORS["green_bg"], "MCP実行済み"),
        ("Obsidian", "ローカルvault生成\nADR / Prompt / Meeting導線", COLORS["panel"], "完了"),
    ]
    for idx, (title, note, fill, status) in enumerate(lanes):
        x = 0.78 + idx * 3.08
        add_rect(slide, x, 2.05, 2.68, 2.72, fill=fill, line=COLORS["line"])
        add_chip(slide, status, x + 0.22, 2.28, 1.35, fill=COLORS["white"], text=COLORS["blue_dark"])
        add_text(slide, title, x + 0.22, 2.82, 2.2, 0.32, size=16, color=COLORS["ink"], bold=True)
        add_text(slide, note, x + 0.22, 3.35, 2.18, 0.72, size=11, color=COLORS["muted"])
    add_bullets(
        slide,
        [
            "NotebookLMはプレゼンの草案作成に使い、AIエージェントの開発入力にもする。",
            "Slackは投稿先と共有範囲の社長確認後に実送信へ進める。",
            "Notionは議事録・意思決定・バックログの公式台帳候補、Obsidianはローカル思考メモ候補。",
        ],
        0.92,
        5.0,
        11.3,
        0.66,
        size=14,
    )
    add_evidence_panel(slide, ["Notion evidence page: https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951", "Slack draft: exports/knowledge_flow/slack_ceo_update.md", "Obsidian vault: exports/knowledge_flow/obsidian_vault/"], y=5.92)

    # 5
    slide = prs.slides.add_slide(blank)
    add_header(slide, 5, "NotebookLM to PPTX", "NotebookLMからPPTXへ", source_note)
    add_flow_box(slide, 1.0, 2.05, "docs/ + WBS", "公式手順・WBSを同期", COLORS["panel"])
    add_arrow(slide, 3.48, 2.34)
    add_flow_box(slide, 3.95, 2.05, "Google Docs", "Workspace所有で22件", COLORS["sky"])
    add_arrow(slide, 6.43, 2.34)
    add_flow_box(slide, 6.9, 2.05, "NotebookLM CLI", "要約・QA・8枚構成", COLORS["green_bg"])
    add_arrow(slide, 9.38, 2.34)
    add_flow_box(slide, 9.85, 2.05, "PowerPoint", "社長説明用PPTX", COLORS["amber_bg"])
    add_bullets(
        slide,
        [
            "NotebookLM CLIで取得したCEO Slide Outlineを、説明用PPTXのストーリー骨子に反映。",
            "PPTXは編集可能なPowerPointファイルとしてexports配下に保存し、Driveにもアップロード対象化。",
            "artifact-tool runtimeはこのWindowsシェルで解決できないため、PPTX組版はpython-pptxで代替。",
        ],
        1.02,
        3.85,
        10.8,
        0.92,
        size=15,
    )
    add_evidence_panel(slide, [f"NotebookLM notebook: {context['notebook_id']}", "Outline: exports/knowledge_flow/notebooklm_ceo_slide_outline.md", "Generator: scripts/generate_ceo_presentation_deck.py"])

    # 6
    slide = prs.slides.add_slide(blank)
    add_header(slide, 6, "Decision Matrix", "サービス方向性の選択肢", source_note)
    add_option_card(slide, 0.76, "A. AIフィット診断支援", "営業 / 人材担当 / エンジニア", "採用・SES・案件配属の効率化", "デモの診断体験を磨く")
    add_option_card(slide, 4.78, "B. Workspace連携型PM支援", "経営 / PM / 現場責任者", "進捗・報告・予定同期の高速化", "WBS/Calendar同期を商品化")
    add_option_card(slide, 8.8, "C. AI PoC高速構築支援", "新規事業 / 企画 / 開発責任者", "検証回数と提案速度を増やす", "NotebookLM/Docs連携を型化")
    add_bullets(
        slide,
        [
            "6/2では最初の適用業務と最初に見せる相手を決める。",
            "正式企画は決め打ちせず、社長判断後にWBSとロードマップへ反映する。",
        ],
        0.92,
        4.95,
        11.2,
        0.5,
        size=15,
    )
    add_evidence_panel(slide, ["Decision pack: docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md", "WBS tasks: T605 / T611 / T623 / T615"])

    # 7
    slide = prs.slides.add_slide(blank)
    add_header(slide, 7, "Risks and Boundaries", "運用・リスク論点と未完了項目", source_note)
    risks = [
        ("公開URL", "社長共有済み。UIデグレは許容しない。", "Public Demo Guardをpush前後で実行"),
        ("Slack", "CLI未検出、送信MCP未露出。", "投稿先と共有範囲をIssue #2で管理"),
        ("GitHub Project", "read:project / project scope不足。", "Issue #8でOAuth復旧後に配置"),
        ("外部投入情報", "認証情報・個人情報・未承認顧客情報は投入禁止。", "docs/とWBSに安全ルールを明記"),
    ]
    y = 1.82
    add_rect(slide, 0.72, y, 11.9, 0.46, fill=COLORS["blue_dark"], line=COLORS["blue_dark"])
    add_text(slide, "論点", 0.96, y + 0.11, 1.4, 0.18, size=9, color=COLORS["white"], bold=True)
    add_text(slide, "現状", 2.5, y + 0.11, 4.5, 0.18, size=9, color=COLORS["white"], bold=True)
    add_text(slide, "次の扱い", 7.42, y + 0.11, 4.5, 0.18, size=9, color=COLORS["white"], bold=True)
    for idx, (topic, status, action) in enumerate(risks):
        row_y = y + 0.55 + idx * 0.72
        add_rect(slide, 0.72, row_y, 11.9, 0.62, fill=COLORS["panel"], line=COLORS["line"])
        add_text(slide, topic, 0.96, row_y + 0.15, 1.35, 0.2, size=11, color=COLORS["ink"], bold=True)
        add_text(slide, status, 2.5, row_y + 0.12, 4.45, 0.24, size=10, color=COLORS["muted"])
        add_text(slide, action, 7.42, row_y + 0.12, 4.45, 0.24, size=10, color=COLORS["ink"])
    add_evidence_panel(slide, ["GitHub Project check: gh project list -> missing read:project", "Slack check: local slack CLI not found; connector send tool not exposed", "Issue #8 / #2で残課題化"])

    # 8
    slide = prs.slides.add_slide(blank)
    add_header(slide, 8, "Next Actions", "次アクションとWBSへの即時反映", source_note)
    steps = [
        ("5/22", "PPTX生成", "NotebookLM outlineをPowerPoint化"),
        ("5/24", "権限確認", "Slack / GitHub Projectの復旧確認"),
        ("5/30", "判断材料レビュー", "社長説明資料の最終確認"),
        ("6/1", "最終リハーサル", "公開URL / WBS / Calendar / 資料確認"),
        ("6/2", "社長判断", "決定事項をWBSへ即時反映"),
    ]
    x0 = 0.82
    for idx, (date, title, note) in enumerate(steps):
        x = x0 + idx * 2.48
        add_rect(slide, x, 2.05, 2.0, 1.72, fill=COLORS["panel"], line=COLORS["line"])
        add_chip(slide, date, x + 0.26, 2.25, 0.78, fill=COLORS["sky"], text=COLORS["blue_dark"])
        add_text(slide, title, x + 0.24, 2.76, 1.5, 0.26, size=12, color=COLORS["ink"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, note, x + 0.2, 3.14, 1.58, 0.34, size=8, color=COLORS["muted"], align=PP_ALIGN.CENTER)
        if idx < len(steps) - 1:
            add_arrow(slide, x + 2.04, 2.72)
    add_bullets(
        slide,
        [
            "社長に決めてもらうこと: 最初の業務課題、最初の利用者、公式化する連携、公開範囲。",
            "決定直後にやること: WBS・Calendar・Issues・Docsへ反映し、次回レビュー日を固定。",
            "保留にすること: サービス名、課金、外部共有範囲、Slack/Notionの正式運用範囲。",
        ],
        0.92,
        4.35,
        11.25,
        0.82,
        size=15,
    )
    add_evidence_panel(slide, ["WBS: data/WBS.tsv / docs/WBS.md", "Calendar sync: scripts/sync_wbs_to_calendar.py", "Issue tracking: GitHub Issues #1-#11/#13/#14/#16"])


def verify_pptx(path: Path, expected_slides: int) -> None:
    if not path.exists() or path.stat().st_size < 10_000:
        raise RuntimeError(f"PPTX was not created or is too small: {path}")
    with zipfile.ZipFile(path) as package:
        slide_parts = [
            name for name in package.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
    if len(slide_parts) != expected_slides:
        raise RuntimeError(f"Expected {expected_slides} slides, found {len(slide_parts)}")


def write_summary(context: dict[str, Any]) -> None:
    content = f"""# Mighty Skill-Bridge CEO Presentation Deck

Generated: {jst_now().isoformat(timespec="seconds")}

## Output

- PPTX: `exports/knowledge_flow/{PPTX_FILE.name}`
- Google Drive: {context.get('pptx_drive_url') or 'not uploaded yet'}
- Generator: `scripts/generate_ceo_presentation_deck.py`
- NotebookLM outline: `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- NotebookLM notebook: `{context['notebook_id']}`
- Workspace account: `{context['account']}`

## Slide List

1. 本日決めたいこと
2. 現在の到達点と公開デモ
3. Google Workspaceで進捗が回る基盤
4. 開発ナレッジ連携の実績とデモ
5. NotebookLMからPPTXへ
6. サービス方向性の選択肢
7. 運用・リスク論点と未完了項目
8. 次アクションとWBSへの即時反映

## Tooling Notes

- NotebookLM CLI produced the source outline and agent brief.
- The local shell could not resolve `@oai/artifact-tool/presentation-jsx`, so the editable PowerPoint was assembled with `python-pptx`.
- The deck intentionally avoids deciding the actual service content before the 2026-06-02 CEO meeting.
"""
    SUMMARY_FILE.write_text(content, encoding="utf-8")


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_json(EXPORT_DIR / "manifest.json")
    docs_manifest = load_json(EXPORT_DIR / "notebooklm_docs_manifest.json")
    drive_docs = load_json(EXPORT_DIR / "google_drive_workspace_docs.json")
    outline = load_json(EXPORT_DIR / "notebooklm_ceo_slide_outline.json")

    context = {
        "account": drive_docs.get("account") or docs_manifest.get("account") or "k-umezawa@ml-mightylink.com",
        "notebook_id": outline.get("notebook_id") or docs_manifest.get("notebook_id") or "75521ea6-6b9b-47b2-9508-50050d8ab2d5",
        "source_count": len(docs_manifest.get("google_docs", {})) or 14,
        "wbs_total": get_nested(manifest, "summary", "total", default=72),
        "pptx_drive_url": get_nested(drive_docs, "files", "ceo_presentation_pptx", "url", default=""),
    }

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    build_slides(prs, context)
    prs.save(PPTX_FILE)

    verify_pptx(PPTX_FILE, expected_slides=8)
    write_summary(context)

    deck_manifest = {
        "generated_at_jst": jst_now().isoformat(timespec="seconds"),
        "account": context["account"],
        "notebook_id": context["notebook_id"],
        "source_outline": "exports/knowledge_flow/notebooklm_ceo_slide_outline.md",
        "source_count": context["source_count"],
        "tooling": {
            "outline": "NotebookLM CLI",
            "pptx_generator": "python-pptx",
            "artifact_tool_status": "not available from the local Windows shell",
        },
        "outputs": {
            "pptx": str(PPTX_FILE.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "summary": str(SUMMARY_FILE.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "google_drive_url": context.get("pptx_drive_url") or None,
        },
        "slide_count": 8,
    }
    MANIFEST_FILE.write_text(json.dumps(deck_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[+] CEO presentation deck generated.")
    print(f"[*] PPTX: {PPTX_FILE.relative_to(PROJECT_ROOT)}")
    print(f"[*] Summary: {SUMMARY_FILE.relative_to(PROJECT_ROOT)}")
    print(f"[*] Manifest: {MANIFEST_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
