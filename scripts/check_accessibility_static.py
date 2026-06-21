"""Static accessibility guard for the public demo HTML.

This check complements axe/Lighthouse-style runtime scans by verifying the
project-specific landmarks, labels, and ARIA state hooks that must stay in the
single-page public demo.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "index.html"


def _contains(pattern: str, html: str) -> bool:
    return re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL) is not None


def check_index_html(path: Path = INDEX_HTML) -> dict[str, object]:
    path = path.resolve()
    html = path.read_text(encoding="utf-8")
    checks: list[tuple[str, bool, str]] = [
        (
            "skip_link",
            '<a class="skip-link" href="#top">' in html and '<main id="top" tabindex="-1">' in html,
            "Skip link must move keyboard users to the main content landmark.",
        ),
        (
            "primary_navigation_target",
            '<nav class="nav-links" id="primary-navigation" aria-label="Primary navigation">' in html,
            "Primary navigation needs a stable aria label and id for mobile controls.",
        ),
        (
            "touch_target_css",
            ".nav-links a,\n        .language-switch a" in html
            and "min-height: 32px;" in html
            and "min-width: 32px;" in html,
            "Navigation and language links must keep WCAG 2.2 AA touch target sizing.",
        ),
        (
            "keyboard_focus_css",
            "a:focus-visible," in html and "outline: 3px solid var(--blue);" in html,
            "Interactive elements need visible keyboard focus styling.",
        ),
        (
            "engineer_input_label",
            'for="engineer-input"' in html and 'aria-labelledby="engineer-input-heading"' in html,
            "Engineer input must have an explicit label and visible heading association.",
        ),
        (
            "job_input_label",
            'for="job-input"' in html and 'aria-labelledby="job-input-heading"' in html,
            "Job input must have an explicit label and visible heading association.",
        ),
        (
            "feedback_comment_label",
            '<label class="sr-only" for="feedback-comment">Feedback comment</label>' in html,
            "Feedback comment textarea must not rely on placeholder text as its label.",
        ),
        (
            "decorative_hero_video_hidden",
            'id="hero-video-bg"' in html and 'aria-hidden="true" tabindex="-1"' in html,
            "Decorative hero video should be removed from the accessibility tree.",
        ),
        (
            "story_video_named",
            'id="seedance-video"' in html and 'aria-label="AI-generated match story preview video"' in html,
            "Meaningful video preview requires an accessible name.",
        ),
        (
            "radar_canvas_named",
            'id="reportRadarChart" role="img"' in html and "4-axis fit radar chart" in html,
            "Canvas chart requires role=img, an accessible name, and fallback text.",
        ),
        (
            "progressbars_named",
            html.count('role="progressbar"') >= 4
            and all(
                label in html
                for label in [
                    'aria-label="Skill fit score"',
                    'aria-label="Culture fit score"',
                    'aria-label="Growth fit score"',
                    'aria-label="Performing fit score"',
                ]
            ),
            "All visual score bars must expose progressbar semantics.",
        ),
        (
            "tab_semantics",
            'role="tablist"' in html
            and html.count('role="tab"') >= 2
            and html.count('role="tabpanel"') >= 2
            and "aria-selected" in html,
            "Report tabs must expose tablist/tab/tabpanel semantics.",
        ),
        (
            "scroll_region_focusable",
            'class="table-responsive" tabindex="0"' in html
            and "Candidates comparison table" in html,
            "Horizontally scrollable comparison table must be keyboard focusable.",
        ),
        (
            "blank_targets_noopener",
            not _contains(r'target="_blank"(?![^>]*rel="[^"]*\bnoopener\b)', html),
            "Links opening a new tab must include rel=noopener.",
        ),
    ]

    failures = [
        {"id": check_id, "message": message}
        for check_id, passed, message in checks
        if not passed
    ]
    return {
        "source": str(path.relative_to(PROJECT_ROOT)),
        "status": "PASS" if not failures else "FAIL",
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    result = check_index_html()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
