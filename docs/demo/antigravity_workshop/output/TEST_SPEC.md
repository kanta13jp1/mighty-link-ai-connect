# Test Specification: AI Agent Decision Guide

SYNTHETIC_DATA_ONLY

This specification is written before final browser polish. It defines what must remain true as the agent edits the site.

## TS-01 Product scope

The dataset contains exactly five unique products: Codex, Claude Code, Claude Cowork, Kiro, and Antigravity. Old rehearsal products such as Devin, Cursor Agent, Windsurf, and Copilot Workspace must not appear in the current site or dataset.

## TS-02 Official icon provenance

Every product references a local icon file and an HTTPS source URL on an official first-party property. Every local icon exists, is non-empty, and is rendered with meaningful alternative text on product cards.

## TS-03 Version and date evidence

Every profile has a public version label, an ISO date, and a direct official release or changelog URL. Claude Cowork must explicitly state `公開版番号なし（SaaS）`; every other product must expose its current numeric version.

## TS-04 Current official content

Every profile includes a latest update, official video, and official blog item. Each item requires a title, ISO date, and HTTPS URL. The site displays `2026-08-13 JST` as the verification date.

## TS-05 Useful decision depth

Every product provides all 13 decision dimensions defined in `SITE_BRIEF.md`. The comparison UI supports one or two selected products, shows all dimensions, and prevents a third selection.

## TS-06 Honest pricing and limits

Pricing text distinguishes published plan prices from variable usage capacity. Previously invented fixed counts such as `1日100回`, `1日1,000回`, `1日1万回`, or `月3,000 PU` are forbidden.

## TS-07 Source ledger

The page provides a source ledger with documentation, release or changelog, pricing, update, video, blog, and icon provenance links. All factual source hosts must be in the approved first-party domain allowlist.

## TS-08 Accessible interaction

Scenario and comparison buttons expose `aria-pressed`; changing filters and selections is announced through `aria-live`; keyboard focus is visible; reduced-motion preferences are respected.

## TS-09 Responsive layout

At 1440x900 and 390x844, official icons load, primary content is visible, and the page has no horizontal document overflow. The comparison table may scroll inside its own labeled region.

## TS-10 Review and publication

Ten distinct self-review passes must be recorded in `SELF_REVIEW.md`. Automated tests, JavaScript syntax checks, desktop/mobile browser checks, and the GitHub Pages URL must pass before publication is called complete.
