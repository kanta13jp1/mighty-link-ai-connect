# WF-01 · Vertical Hero Stack — Mobile-first

> Subtitle: 1 column / top-to-bottom flow. 縦スクロールで完結。スマホ親和。
> 💡 Rationale: 最小 UI で迷わず Step 1→2→3 を順に体験できる。SES 営業が客先で iPad プレゼン時に強い。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-01` |
| category | mobile-first / hero stack |
| status | spec-ready (visual = Canva slide 2) |
| pick-when | スマホ/iPad 中心、客先プレゼン、最少クリック |
| skip-when | デスクトップ multi-window 運用、複数候補同時管理 |
| output target | `static/wireframes/wf-01.html` (single file) |

## 2. ASCII Layout

```text
┌──────────────────────────── 375 width ────────────────────────────┐
│ [≡]  Mighty Skill-Bridge                                  [⚙]    │
├───────────────────────────────────────────────────────────────────┤
│ Hero: "AIで一瞬にフィット診断"                                    │
│   sub: "経歴と案件を貼るだけ"                                     │
│   [▶ デモ動画 / Seedance]   ←── /api/seedance/video-demo          │
├───────────────────────────────────────────────────────────────────┤
│ Step 1 ─ 経歴書                                                   │
│   [textarea 8 rows]                                               │
│   [📎 Upload PDF/IMG] [✏ Load Sample]                             │
├───────────────────────────────────────────────────────────────────┤
│ Step 2 ─ 案件票                                                   │
│   [textarea 8 rows]                                               │
│   [📎 Upload PDF/IMG] [✏ Load Sample]                             │
├───────────────────────────────────────────────────────────────────┤
│           [  ⚡ Analyze Fit  ]  (full-width CTA)                  │
├───────────────────────────────────────────────────────────────────┤
│ Result (lazy-rendered on success)                                 │
│   [Score gauge: 88 / 100]                                         │
│   [Radar: Skill / Culture / Growth / Performing]                  │
│   [Summary card]                                                  │
│   [QA Accordion x2]                                               │
│   [Roadmap week1 / week2 / week3]                                 │
└───────────────────────────────────────────────────────────────────┘
```

## 3. Component Tree (semantic HTML)

```html
<main class="wf01">
  <header class="wf01__topbar"><button aria-label="menu">≡</button><h1>Mighty Skill-Bridge</h1></header>
  <section class="wf01__hero" aria-labelledby="hero-h">
    <h2 id="hero-h">AI で一瞬にフィット診断</h2>
    <p>経歴と案件を貼るだけ</p>
    <video class="wf01__demo-video" autoplay muted loop playsinline></video>
  </section>
  <section class="wf01__step" aria-labelledby="step1-h">
    <h3 id="step1-h">Step 1 — 経歴書</h3>
    <textarea name="engineer" rows="8" aria-label="engineer profile"></textarea>
    <div class="wf01__step-actions">
      <input type="file" id="engineer-file" hidden>
      <label for="engineer-file" class="btn">📎 Upload</label>
      <button class="btn" data-act="load-sample-engineer">✏ Load Sample</button>
    </div>
  </section>
  <section class="wf01__step" aria-labelledby="step2-h">
    <h3 id="step2-h">Step 2 — 案件票</h3>
    <textarea name="job" rows="8" aria-label="job description"></textarea>
    <div class="wf01__step-actions"> ... same shape ... </div>
  </section>
  <button class="wf01__cta" data-act="analyze">⚡ Analyze Fit</button>
  <section class="wf01__result" aria-live="polite" hidden>
    <div class="wf01__gauge" data-score="0"></div>
    <canvas class="wf01__radar" width="320" height="320"></canvas>
    <article class="wf01__summary"></article>
    <details class="wf01__qa" open></details>
    <details class="wf01__qa"></details>
    <section class="wf01__roadmap"></section>
  </section>
</main>
```

## 4. State Machine

```text
initial ── load-sample ──> filled
filled  ── analyze    ──> analyzing (CTA spinner, disabled)
analyzing ── 200      ──> loaded   (result section revealed, scroll-to-result)
analyzing ── error    ──> error    (toast + CTA re-enabled)
loaded  ── edit-input ──> filled   (result blurred, "Re-analyze" hint)
```

## 5. Data Flow + API contract

1. Step 1 / Step 2 で textarea or upload。クライアント検証: `text || file` のいずれか必須、`text.length >= 30` 推奨警告。
2. `Analyze` クリック → 並列 `POST /api/parse` × 2 (`doc_type=engineer` / `doc_type=job`) → `parsed_text` 取得。
3. → 直列 `POST /api/match` JSON `{engineer_content, job_content}` (parsed_text を渡す)。
4. response.scores を radar に描画、`final_score` を gauge に、`qa[]` を accordion に、`roadmap_week1/2/3` を見出し付き段落に。

## 6. Design Tokens (override on README.md base)

```css
.wf01 { background: var(--c-bg); color: var(--c-text); font-size: var(--fs-body);
        max-width: 480px; margin: 0 auto; padding: var(--s-3); }
.wf01__cta { width: 100%; padding: var(--s-3) var(--s-4); background: var(--c-accent);
             color: var(--c-bg); border-radius: var(--r-md); font-size: var(--fs-h2);
             font-weight: 700; box-shadow: 0 0 24px rgba(0,240,255,0.35); }
.wf01__cta:disabled { opacity: 0.5; cursor: progress; }
```

## 7. Interaction Spec

- Sample ボタン: クライアント local string を textarea へ inject (既存 `loadSampleEngineer()` / `loadSampleJob()` 流用)
- Analyze: parse 2 並列 → match 1。実行中は CTA `aria-busy="true"`、result 隠蔽。
- result reveal: `scrollIntoView({behavior:"smooth", block:"start"})`、`prefers-reduced-motion: reduce` 時は instant。
- 再分析: textarea `input` イベントで result に `.is-stale` class 付与 (opacity 0.4)、CTA テキストを「⚡ Re-analyze」へ。

## 8. A11y

- Step heading は `<h3>`、Result heading は `<h2>` 相当 (実質 h2 想定)。
- CTA `<button>`、disable は `aria-disabled="true"` + `disabled` 両方。
- Result `aria-live="polite"`、長文 summary は `tabindex="0"` で読み上げ移動可。
- contrast: text(#F1F5FF) on bg(#0D0E15) ≈ 17:1 (WCAG AAA)。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 480 (mobile) | 全幅、padding 16px、CTA full-width sticky-bottom 候補 |
| 481-900 (tablet) | max-width 600、padding 24、CTA inline 中央寄せ |
| ≥ 901 (desktop) | max-width 720、左右余白あり、hero 動画は 16:9 リッチ |

## 10. Out of Scope

- 複数候補比較 (→ WF-07)
- ダッシュボード集計 (→ WF-08)
- Drag&Drop (→ WF-05)
- 検索 (→ WF-10)
- 管理者ページ (`/admin` は別系)

## 11. Acceptance Criteria

- [ ] mobile (375x812) で横スクロール 0
- [ ] Analyze → 結果表示まで 5s 以内 (Gemini live) / 3s 以内 (`AI_FORCE_MOCK=1`)
- [ ] Step 1 / Step 2 のクリーン状態と Loaded 状態が視認可能 (DOMContentLoaded で auto-load しない)
- [ ] gauge / radar / summary / qa / roadmap 5 要素が full response で全て描画される
- [ ] keyboard only で Step1 → Step2 → Analyze → Result を一巡完走
- [ ] `prefers-reduced-motion: reduce` で smooth scroll が instant に切り替わる
- [ ] verify_public_demo.py が pass し続ける

## 12. Implementation Prompt (LLM-ready)

```text
You are implementing WF-01 "Vertical Hero Stack" for Mighty Skill-Bridge.

Stack constraints:
- Single HTML file at static/wireframes/wf-01.html
- vanilla JS only, no build step, no framework
- Fetch existing FastAPI endpoints: POST /api/parse (multipart), POST /api/match (json)
- Apply Mighty cyber palette tokens (see docs/wireframes/README.md §Design Tokens)
- Mobile-first, max-width 480px, single column

Behavior: see docs/wireframes/WF-01_vertical_hero_stack.md §4 State Machine + §5 Data Flow.

Acceptance: see §11. Do not modify root index.html or src/index.html. Do not introduce React/Vue/build tools.

Output: complete static/wireframes/wf-01.html with embedded <style> and <script>. Verify locally with:
  python src/app.py
  open http://localhost:8000/static/wireframes/wf-01.html
```

## 13. Starter Snippet (drop-in skeleton)

```html
<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mighty Skill-Bridge — WF-01</title>
<style>
  :root { --c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-text-sub:#C5CAE0;
          --c-accent:#00F0FF;--c-success:#39FF14;--c-danger:#FF3366;--c-border:#2A2D3E;
          --r-md:12px;--s-3:16px;--s-4:24px;--fs-h1:32px;--fs-body:16px; }
  body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
  .wf01{max-width:480px;margin:0 auto;padding:var(--s-3)}
  .wf01 h2{font-size:var(--fs-h1)}
  textarea{width:100%;background:var(--c-surface);color:var(--c-text);
           border:1px solid var(--c-border);border-radius:var(--r-md);padding:var(--s-3);box-sizing:border-box}
  .wf01__cta{width:100%;padding:var(--s-3) var(--s-4);background:var(--c-accent);
             color:var(--c-bg);border:0;border-radius:var(--r-md);font-size:22px;font-weight:700;margin-top:var(--s-3)}
  .wf01__cta[aria-busy="true"]{opacity:.5;cursor:progress}
  .wf01__result[hidden]{display:none}
</style></head><body>
<main class="wf01">
  <h2>AI で一瞬にフィット診断</h2>
  <p>経歴と案件を貼るだけ</p>
  <section><h3>Step 1 — 経歴書</h3><textarea id="engineer" rows="8"></textarea></section>
  <section><h3>Step 2 — 案件票</h3><textarea id="job" rows="8"></textarea></section>
  <button class="wf01__cta" id="analyze">⚡ Analyze Fit</button>
  <section class="wf01__result" id="result" aria-live="polite" hidden></section>
</main>
<script>
const $ = (s) => document.querySelector(s);
async function parseDoc(text, doc_type) {
  const fd = new FormData(); fd.append("text", text); fd.append("doc_type", doc_type);
  const r = await fetch("/api/parse", {method:"POST", body: fd});
  if (!r.ok) throw new Error("parse "+doc_type+" failed");
  return r.json();
}
async function match(eng, job) {
  const r = await fetch("/api/match", {method:"POST", headers:{"content-type":"application/json"},
    body: JSON.stringify({engineer_content: eng, job_content: job})});
  if (!r.ok) throw new Error("match failed");
  return r.json();
}
$("#analyze").addEventListener("click", async (ev) => {
  const cta = ev.currentTarget; cta.setAttribute("aria-busy","true"); cta.disabled = true;
  try {
    const eng = $("#engineer").value.trim(), job = $("#job").value.trim();
    if (!eng || !job) throw new Error("両方の入力が必要です");
    const [p1, p2] = await Promise.all([parseDoc(eng,"engineer"), parseDoc(job,"job")]);
    const m = await match(p1.parsed_text || eng, p2.parsed_text || job);
    const res = $("#result"); res.hidden = false;
    res.innerHTML = `<h2>Score: ${m.final_score}</h2><pre>${JSON.stringify(m.scores,null,2)}</pre>
                     <p>${m.summary}</p>`;
    res.scrollIntoView({behavior:"smooth"});
  } catch (e) { alert(e.message); }
  finally { cta.removeAttribute("aria-busy"); cta.disabled = false; }
});
</script></body></html>
```
