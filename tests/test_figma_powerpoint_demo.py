import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "docs" / "demo" / "antigravity_workshop"
PROMPT = WORKSHOP / "PROMPT_12_FIGMA_POWERPOINT.txt"
GUIDE = WORKSHOP / "FIGMA_POWERPOINT_DEMO.md"
README = WORKSHOP / "README.md"
PPTX = ROOT / "exports" / "mighty_skill_bridge_antigravity2_figma_mcp_powerpoint_demo_2026.pptx"


def test_prompt_is_copyable_and_fail_closed() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "編集可能なFigma Slides" in text
    assert "team::1404381379512110171" in text
    assert "project ID: 264549730" in text
    assert "上記と異なるteamやprojectへは作成しない" in text
    assert "文字切れ、重なり、キャンバス外要素がない" in text
    assert "PowerPointへの書き出しはまだ実行しない" in text
    assert not re.search(r"AIzaSy[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]", text)


def test_guide_places_figma_mcp_in_the_five_minute_main_slot() -> None:
    text = GUIDE.read_text(encoding="utf-8")

    assert "Web制作を主役とする30分デモ" in text
    assert "Antigravity 2.0 + Figma MCP + PowerPoint 5分デモ" in text
    assert "90秒復旧" in text
    assert "kanta13jp1's team" in text
    assert "project ID: `264549730`" in text
    assert "Export-from-Figma-Slides" in text
    readme = README.read_text(encoding="utf-8")
    assert "PROMPT_12_FIGMA_POWERPOINT.txt" in readme
    assert "20:00-25:00" in readme
    assert "Antigravity IDE、CLI、SDKは30分本編では操作しません" in readme


def test_antigravity2_powerpoint_has_all_sourced_slides() -> None:
    assert PPTX.is_file()

    with zipfile.ZipFile(PPTX) as archive:
        names = archive.namelist()
        slide_names = [
            name
            for name in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes_names = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        notes_xml = "".join(
            archive.read(name).decode("utf-8") for name in notes_names
        )

    assert len(slide_names) == 36
    assert len(notes_names) == 36
    assert notes_xml.count("[Sources]") == 36
