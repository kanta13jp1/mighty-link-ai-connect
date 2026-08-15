import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "docs" / "demo" / "antigravity_workshop"
PROMPT = WORKSHOP / "PROMPT_12_FIGMA_POWERPOINT.txt"
GUIDE = WORKSHOP / "FIGMA_POWERPOINT_DEMO.md"
README = WORKSHOP / "README.md"
PPTX = ROOT / "exports" / "mighty_skill_bridge_figma_powerpoint_demo_2026.pptx"


def test_prompt_is_copyable_and_fail_closed() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "編集可能なFigma Slides" in text
    assert "複数候補がある場合" in text
    assert "文字切れ、重なり、キャンバス外要素が0件" in text
    assert "PPTXへの書き出しは実行せず" in text
    assert not re.search(r"AIzaSy[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]", text)


def test_guide_keeps_figma_in_the_optional_slot() -> None:
    text = GUIDE.read_text(encoding="utf-8")

    assert "30分のAntigravity本編を変更せず" in text
    assert "90秒復旧" in text
    assert "kanta13jp1's team" in text
    assert "tokyofigma01" in text
    assert "Export-from-Figma-Slides" in text
    assert "PROMPT_12_FIGMA_POWERPOINT.txt" in README.read_text(encoding="utf-8")


def test_backup_powerpoint_has_five_sourced_slides() -> None:
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

    assert len(slide_names) == 5
    assert len(notes_names) == 5
    assert notes_xml.count("[Sources]") == 5
