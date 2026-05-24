# Wireframes — Implementation-Ready Spec Pack

作成日: 2026-05-24
オーナー: Claude Code レーン (docs / spec)
対象 WBS: T658-wireframe-deck / T658-mcp-extend
関連:
[CEO_PRESENTATION_PREP](../CEO_PRESENTATION_PREP_2026-06-02.md) /
[MCP_CANVA_FIGMA_SETUP_GUIDE](../MCP_CANVA_FIGMA_SETUP_GUIDE_2026-06-02.md) §4.7 /
Canva v2 deck: <https://docs.google.com/presentation/d/1JKu7tAw1h4BqXMAsF41qolbQPUKj8KLW/edit>

---

## このパックの位置づけ

[Canva v2 wireframe deck](https://docs.google.com/presentation/d/1JKu7tAw1h4BqXMAsF41qolbQPUKj8KLW/edit) は社長判断用の **visual mockup**。本パックは同じ 10 パターンを **AI に渡してそのまま実装できる粒度の spec** に展開したもの。

各 spec は以下を含むため、社長 6/2 判断後に **「@docs/wireframes/WF-XX_*.md を実装」**とプロンプトすれば、現プロト (`FastAPI + vanilla HTML/JS`) 上で実装着手できる:

1. **Identity** — id / category / pick-when マトリクス
2. **ASCII Layout** — テキスト wireframe
3. **Component Tree** — semantic HTML skeleton
4. **State Machine** — initial → loading → loaded → error
5. **Data Flow + API contract** — どの `src/app.py` endpoint を叩くか
6. **Design Tokens** — Mighty cyber palette + per-WF override
7. **Interaction Spec** — event / trigger / debounce
8. **A11y** — ARIA role / keyboard nav
9. **Responsive** — desktop / tablet / mobile breakpoint
10. **Out of Scope** — 意図的に含めない要素
11. **Acceptance Criteria** — pass/fail checklist
12. **Implementation Prompt** — LLM-ready コピペ用
13. **Starter Snippet** — drop-in HTML 骨格

---

## Stack 前提

| 項目 | 値 |
| --- | --- |
| **backend** | FastAPI (`src/app.py`、2065 行) |
| **frontend** | vanilla HTML/JS single-file (`index.html` + `src/index.html` ミラー) |
| **build** | なし (Python serve only) |
| **public URL** | <https://kanta13jp1.github.io/mighty-link-ai-connect/> |
| **local dev** | `python src/app.py` → `http://localhost:8000/` |
| **public demo guard** | `python scripts/verify_public_demo.py` を CI で実行 |

実装時の **強い制約** (現プロト準拠):
- 新 build step (webpack/vite) 追加禁止 — single HTML + CDN script のみ
- 新 framework (React/Vue) 追加禁止 — vanilla JS
- `src/index.html` と root `index.html` は必ず双方更新 ([scripts/render_seedance_video_demo_ui.py](../../scripts/render_seedance_video_demo_ui.py) を流用)
- `verify_public_demo.py` が探すマーカー (`Mighty Skill-Bridge` / `/api/parse` / `/api/match` 等) を消さない

---

## 既存 API contract (全 WF が利用)

### `POST /api/parse`

`multipart/form-data`:

| field | type | required | note |
| --- | --- | --- | --- |
| `text` | string | file 未指定時は必須 | 経歴書 / 案件票テキスト |
| `file` | binary | text 未指定時は必須 | PDF / image / txt |
| `doc_type` | string | required | `"engineer"` または `"job"` |

response (200):

```json
{
  "parsed_text": "...",
  "structured": { "name": "...", "title": "...", "skills": {...}, "years": 5, ... },
  "audit": { "ai_mode": "live"|"fallback", "fallback_reason": "..." }
}
```

### `POST /api/match`

`application/json`:

```json
{
  "engineer_content": "...",
  "job_content": "..."
}
```

response (200):

```json
{
  "final_score": 50-100,
  "scores": {"skill": int, "culture": int, "growth": int, "performing": int},
  "summary": "...",
  "qa": [{"question":"...","answer":"...","tip":"..."}, ...],
  "roadmap_week1": "...",
  "roadmap_week2": "...",
  "roadmap_week3": "...",
  "audit": { ... }
}
```

その他: `GET /api/health` / `GET /api/audit/recent` / `GET /api/knowledge-flow/status` / `POST /api/knowledge-flow/generate` / `POST /api/seedance/video-demo` / `GET /api/admin/usage`

---

## Mighty cyber palette (全 WF 共通 design token)

```css
:root {
  --c-bg:        #0D0E15;  /* cyber black */
  --c-surface:   #161824;  /* deep navy */
  --c-text:      #F1F5FF;  /* cool white */
  --c-text-sub:  #C5CAE0;  /* gray white */
  --c-accent:    #00F0FF;  /* neon blue */
  --c-success:   #39FF14;  /* neon green */
  --c-danger:    #FF3366;  /* neon red */
  --c-border:    #2A2D3E;
  --r-sm: 6px; --r-md: 12px; --r-lg: 20px;
  --s-1: 4px; --s-2: 8px; --s-3: 16px; --s-4: 24px; --s-5: 40px;
  --fs-h1: 32px; --fs-h2: 22px; --fs-body: 16px; --fs-sm: 13px;
}
```

Breakpoints: `--bp-mobile: 480px` / `--bp-tablet: 900px` / `--bp-desktop: 1280px`.

---

## 20 patterns index

| # | spec | 強み | 弱み | 想定ユーザー |
| --- | --- | --- | --- | --- |
| **WF-01** | [Vertical Hero Stack](WF-01_vertical_hero_stack.md) | mobile-first / iPad プレゼン | desktop 余白多 | SES 営業 |
| **WF-02** | [Split Form (現行)](WF-02_split_form.md) | desktop 視覚対置 | mobile 縦長化 | デスクトップ HR |
| **WF-03** | [Step Wizard](WF-03_step_wizard.md) | 初回ユーザー親和 | 慣れると遅い | 社内人事 |
| **WF-04** | [Conversational Chat](WF-04_conversational_chat.md) | 応募者親和 / 履歴 | 高速処理に不向き | 応募者本人 |
| **WF-05** | [DnD 4 Quadrant](WF-05_dnd_quadrant.md) | 複数並列管理 | 学習コスト高 | 中規模人事 |
| **WF-06** | [Kanban Pipeline](WF-06_kanban_pipeline.md) | 進捗追跡標準 | 入力 UI 別途要 | リクルーター |
| **WF-07** | [Comparison Table](WF-07_comparison_table.md) | 経営報告最強 | 入力 UI 別途要 | 最終決裁者 |
| **WF-08** | [Dashboard Tiles](WF-08_dashboard_tiles.md) | 経営層一覧 | drill-down 別途 | 社長 / 経営層 |
| **WF-09** | [Inline Live Preview](WF-09_inline_live_preview.md) | AI ライブ感最大 | API 課金重い | 社長デモ専用 |
| **WF-10** | [Search Catalog](WF-10_search_catalog.md) | データ蓄積後の入口 | 初期データ 0 で空 | リクルーター日常 |
| **WF-11** | Voice Interview (impl 直接、spec md なし) | 音声入力 / 電話面接の感触 | ノイズ / 認識精度 | 応募者本人 |
| **WF-12** | Calendar Timeline (impl 直接) | 配属計画の時間軸が一目 | 8 週固定、ズーム未対応 | 配属計画 PM |
| **WF-13** | Map / Geo View (impl 直接) | 通勤距離を判定軸に | 地図は SVG 簡易、本物の Maps API 未統合 | 勤務地依存案件 |
| **WF-14** | Spreadsheet Editor (impl 直接) | パワーユーザーが即編集できる | formula は擬似的 | パワーユーザー HR |
| **WF-15** | Card Swipe (impl 直接) | 1 件ずつ集中判断 | 並列比較できない | 1 件ずつ集中したい判定者 |
| **WF-16** | Org Tree (impl 直接) | 階層ビューで配置全体把握 | 横スクロール深いと辛い | 組織配置責任者 |
| **WF-17** | A vs B Diff (impl 直接) | 2 候補絞り込みに特化 | 3+ 同時比較は WF-07 へ | 最終 2 名から 1 名選定 |
| **WF-18** | Notification Inbox (impl 直接) | event 駆動運用に強い | 通知設定 UI 別途要 | 常駐運用担当 |
| **WF-19** | Onboarding Tour (impl 直接) | empty state を歓迎に変換 | 慣れたら邪魔 | 新規ユーザー初回 |
| **WF-20** | Print Report (impl 直接) | A4 PDF / 経営層配布資料 | インタラクションなし | 経営層配布 |

> WF-01〜WF-10 は専用 spec md (`WF-XX_*.md`) を持ちますが、WF-11〜WF-20 は impl HTML を直接読んで仕様を把握する想定です。
> 必要に応じて `docs/wireframes/WF-11_voice_interview.md` 等を follow-up セッションで追加可能です。

---

## 使い方 (AI 実装プロンプト)

### Claude Code / Codex セッションで

```text
@docs/wireframes/WF-03_step_wizard.md を実装してください。
出力は exports/wireframes/wf-03.html 単一ファイル。
既存 src/app.py の /api/parse + /api/match を fetch で呼び出してください。
verify_public_demo.py が破壊されないよう、root index.html は触らないでください。
```

### 自動化 (将来)

```powershell
python scripts/generate_wireframe_impl.py --wf 03 --out exports/wireframes/wf-03.html
```

(`generate_wireframe_impl.py` は本パック実装後、必要時に Codex レーンで作成想定)

### 機械可読版

[`exports/wireframes/wireframes_spec.json`](../../exports/wireframes/wireframes_spec.json) に 10 パターン全 spec を統合。プログラムから一括処理する場合 / LLM プロンプトに一気に渡す場合に利用。

---

## 受け入れ基準 (本パック自体)

- [x] 10 WF 全 spec が同一構造 (13 セクション) で書かれている
- [x] 既存 API 仕様 (`/api/parse` / `/api/match`) と整合
- [x] Mighty cyber palette を design token で共通化
- [x] 各 spec に LLM-ready Implementation Prompt と Starter Snippet を含む
- [x] `verify_public_demo.py` を破壊しない (root index.html を変更しない)
- [x] `exports/wireframes/wireframes_spec.json` 同梱で機械可読化済
