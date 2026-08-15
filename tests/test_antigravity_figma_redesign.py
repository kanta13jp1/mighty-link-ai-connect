from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "exports" / "mighty_skill_bridge_antigravity_user_guide_2026_figma_redesign.pptx"
GUIDE = ROOT / "docs" / "demo" / "antigravity_workshop" / "FIGMA_POWERPOINT_DEMO.md"
GENERATOR = ROOT / "scripts" / "generate_antigravity_user_guide_figma_redesign.mjs"
FIGMA_URL = "https://www.figma.com/slides/t1LgWfEHQKTAkCxsxUFkgD"
FIGMA_PROJECT_URL = (
    "https://www.figma.com/files/team/1404381379512110171/project/264549730"
)


def test_figma_redesign_assets_are_documented() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    assert "kanta13jp1's team" in guide
    assert "Team project" in guide
    assert FIGMA_URL in guide
    assert FIGMA_PROJECT_URL in guide
    assert DECK.name in guide
    assert GENERATOR.name in guide


def test_generator_preserves_source_and_uses_artifact_tool() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "PresentationFile.importPptx" in source
    assert "PresentationFile.exportPptx" in source
    assert FIGMA_URL in source
    assert "speakerNotes.append" in source


def test_figma_redesign_deck_has_all_slides_and_sources() -> None:
    assert DECK.exists()
    assert DECK.stat().st_size > 1_000_000

    with ZipFile(DECK) as archive:
        names = archive.namelist()
        slides = [
            name
            for name in names
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
        notes = [
            name
            for name in names
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        ]
        note_text = "\n".join(
            archive.read(name).decode("utf-8", errors="replace") for name in notes
        )

    assert len(slides) == 36
    assert len(notes) == 36
    assert note_text.count("[Sources]") == 36
    assert FIGMA_URL in note_text
