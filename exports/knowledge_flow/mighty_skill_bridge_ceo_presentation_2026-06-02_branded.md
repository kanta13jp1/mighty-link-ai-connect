# Mighty Skill-Bridge CEO Presentation Deck (Branded)

Generated: 2026-05-24T01:14:47.916380+09:00

## Output

- PPTX: `exports\knowledge_flow\mighty_skill_bridge_ceo_presentation_2026-06-02_branded.pptx`
- Generator: `scripts/generate_branded_ceo_deck.py`
- Source outline: `exports/knowledge_flow/notebooklm_ceo_slide_outline.md` (NotebookLM CLI 22 sources)
- Brand palette: Mighty Skill-Bridge (Seedance cinematic) — cyber black + neon blue + neon green

## Slides

1. Title slide (Brand cover)
2. 本日決めたいこと
3. 現在の到達点と公開デモ
4. Google Workspace で進捗が回る基盤
5. 開発ナレッジ連携の実績とデモ
6. サービス方向性の選択肢
7. 運用・リスクの論点と公開範囲
8. 6/2 以降の優先開発機能と体制
9. 次アクションと WBS への即時反映

## Design notes

- Cyber black background (#0d0e15) with neon blue/green/red accents
- Slide number badge + accent underline header
- 60/40 split: KEY POINTS panel (left) + EVIDENCE panel (right)
- Highlighted CTA box at bottom for 社長への質問
- Yu Gothic UI for Japanese body + Consolas for accents/IDs

## Companion

`mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` (NotebookLM-CLI default style)
is the source-of-truth content. This `_branded.pptx` is the visual upgrade for
社長プレゼン 当日。Both decks have the same content; only styling differs.

## Next

- Run `python scripts/upload_notebooklm_docs_to_drive.py` to push to Drive (manual add to upload list if needed)
- Or use Canva MCP (HANDOFF-14b) for further refinement once OAuth is done
