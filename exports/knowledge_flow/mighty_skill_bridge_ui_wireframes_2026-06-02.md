# Mighty Skill-Bridge UI Wireframes — 10 Patterns

Generated: 2026-05-24T02:52:01.403677+09:00

## Output

- PPTX: `exports/knowledge_flow/mighty_skill_bridge_ui_wireframes_2026-06-02.pptx`
- Slides: 1 title + 10 wireframes = 11 slides
- Style: greyscale wireframe (no brand colors — focus on layout pattern)

## Companion

- Figma file (empty container, awaiting MCP rate limit reset):
  https://www.figma.com/design/aiQt3c1Cenru4x6GMcLuL5

## 10 Patterns

01. **Vertical Hero Stack — Mobile-first** — 1 column / top-to-bottom flow. 縦スクロールで完結。スマホ親和。
    _Rationale_: 最小 UI で迷わず Step 1→2→3 を順に体験できる。SES 営業が客先で iPad プレゼン時に強い。
02. **Split Form — Profile vs Job (Current)** — 2 列並列入力 / 中央 Analyze CTA。現行 UI のベース。
    _Rationale_: 比較対象を視覚的に対置。デスクトップでの広い画面前提。
03. **Step Wizard — 4-step Progress Flow** — 経歴 → 案件 → 確認 → 結果。1 ステップずつ集中。
    _Rationale_: 初めて使う社内人事担当が迷わない。各ステップで Help が出せる。
04. **Conversational Chat — AI Interview** — AI が質問 / ユーザーが回答 / 最終 fit を結果バブルで提示。
    _Rationale_: 応募者本人が直接使う場合に親しみやすい。チャット履歴で説明責任。
05. **Drag & Drop Cards — 4 Quadrant Workspace** — Engineers / Jobs / Matches / Reports の 4 象限。カード DnD。
    _Rationale_: 中規模の人事チームが複数案件 × 複数候補を同時管理。
06. **Pipeline Board — Kanban for Recruiters** — 候補 → 評価中 → 推薦 → 配属済。Score badge 付きカード。
    _Rationale_: リクルーター業務の標準ビュー。複数案件並列追跡しやすい。
07. **Comparison Table — Multi-candidate Matrix** — 候補 (rows) × 評価軸 (cols)。color-coded score。
    _Rationale_: 経営報告/最終決裁で最強。1 画面で 5-10 候補を比較できる。
08. **Dashboard Tiles — Exec Overview** — 6 タイル: 本日マッチ / Score 分布 / Skill Gap / Recent / Queue / Metrics。
    _Rationale_: 社長 / 経営層が一目で全体把握。週次レビューで使う。
09. **Inline Preview — Live Suggestions** — 入力中に右パネルへリアルタイム fit / 候補をストリーミング表示。
    _Rationale_: AI ライブ感を最大化。社長デモで「打ちながら結果が変わる」を見せる。
10. **Search-First Catalog — Engineer/Job Library** — 検索バー + フィルタ → グリッドカード → 詳細モーダル。
    _Rationale_: 蓄積データが増えた後の "リクルーターの日常入口"。検索駆動。
