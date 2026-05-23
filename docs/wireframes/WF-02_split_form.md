# WF-02 · Split Form — Profile vs Job (現行 UI のベース)

> Subtitle: 2 列並列入力 / 中央 Analyze CTA。現行 UI のベース。
> 💡 Rationale: 比較対象を視覚的に対置。デスクトップでの広い画面前提。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-02` |
| category | desktop-first / split form |
| status | spec-ready (visual = Canva slide 3、現行 `index.html` と最も近い) |
| pick-when | デスクトップ常用、左右視覚比較、現行から最小変更 |
| skip-when | スマホ中心、片方の入力が長文 |
| output target | `static/wireframes/wf-02.html` |

## 2. ASCII Layout

```text
┌────────────────────── 1280+ width ──────────────────────────────────┐
│  Mighty Skill-Bridge                              [Admin] [⚙]       │
├──────────────────────────┬──────────────────────────────────────────┤
│ 経歴書 (Profile)         │ 案件票 (Job)                              │
│ [textarea 14 rows]       │ [textarea 14 rows]                       │
│ [📎 Upload] [Load Sample]│ [📎 Upload] [Load Sample]                │
├──────────────────────────┴──────────────────────────────────────────┤
│                  ┌─────────────────────────┐                        │
│                  │   ⚡ Analyze Fit        │  (centered)             │
│                  └─────────────────────────┘                        │
├─────────────────────────────────────────────────────────────────────┤
│ Result band (full width)                                            │
│   [Gauge 88] [Radar 4-axis]     | Summary text                      │
│   ──────────────────────────────┼──────────────────────────────     │
│   QA accordion x2               | Roadmap week1/2/3                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf02">
  <header><h1>Mighty Skill-Bridge</h1><nav><a href="/admin">Admin</a></nav></header>
  <div class="wf02__grid">
    <section class="wf02__col" aria-labelledby="eng-h">
      <h2 id="eng-h">経歴書</h2>
      <textarea id="engineer" rows="14"></textarea>
      <div class="wf02__col-actions"><label class="btn">📎 Upload<input type="file" hidden></label>
        <button data-act="load-sample-engineer">Load Sample</button></div>
    </section>
    <section class="wf02__col" aria-labelledby="job-h">
      <h2 id="job-h">案件票</h2>
      <textarea id="job" rows="14"></textarea>
      <div class="wf02__col-actions">...same shape...</div>
    </section>
  </div>
  <button class="wf02__cta" data-act="analyze">⚡ Analyze Fit</button>
  <section class="wf02__result" aria-live="polite" hidden>
    <div class="wf02__result-left"><div class="gauge"></div><canvas class="radar"></canvas></div>
    <div class="wf02__result-right"><article class="summary"></article></div>
    <details class="qa" open></details><details class="qa"></details>
    <section class="roadmap"></section>
  </section>
</main>
```

## 4. State Machine

```text
initial ── load-sample ──> filled
filled  ── analyze    ──> analyzing (両 textarea readonly, CTA spinner)
analyzing ── 200      ──> loaded   (result band reveal、no scroll、in-place)
analyzing ── error    ──> error    (toast)
loaded  ── edit       ──> filled-stale (result .is-stale)
```

## 5. Data Flow + API contract

WF-01 と同じ: `Promise.all([/api/parse engineer, /api/parse job])` → `/api/match`。
ただし result は **scroll しない** (in-place reveal)。

## 6. Design Tokens (override)

```css
.wf02 { display: grid; gap: var(--s-4); max-width: 1280px; margin: 0 auto; padding: var(--s-4); }
.wf02__grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-4); }
.wf02__cta { justify-self: center; padding: var(--s-3) var(--s-5);
             background: var(--c-accent); color: var(--c-bg); border-radius: var(--r-lg);
             font-size: var(--fs-h2); font-weight: 700; }
.wf02__result { display: grid; grid-template-columns: 360px 1fr; gap: var(--s-4); }
```

## 7. Interaction Spec

- Tab order: 経歴 textarea → Upload → Sample → 案件 textarea → Upload → Sample → Analyze。
- 並列 Promise.all 中は両 textarea に `readonly` 属性付与 (誤入力防止)。
- Result band 出現時に `wf02__cta` を `wf02__cta--secondary` style へ降格 (背景透明 + neon border)。

## 8. A11y

- 2-column grid は `<section>` x 2 で並列、screen reader 順序 = DOM 順序 (LTR で経歴 → 案件)。
- mobile では grid を 1 列に縮退 (§9 参照)、reading order 維持。
- result-left の gauge / radar は SVG + `role="img" aria-label="Score 88 of 100"` を必須。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 900 (tablet/mobile) | `grid-template-columns: 1fr` (縦積み)、CTA full-width |
| 901-1279 | 2 列 + CTA center |
| ≥ 1280 (desktop) | 2 列 + result band 2 列 (gauge/radar 360px + summary 1fr) |

## 10. Out of Scope

- step progress UI (→ WF-03)
- chat 形式 (→ WF-04)
- 複数案件並列 (→ WF-05/06)

## 11. Acceptance Criteria

- [ ] desktop 1280 で左右 textarea が等幅、CTA 中央
- [ ] mobile 375 で 1 列縦積み、CTA full-width
- [ ] result band reveal で page scroll が発生しない (in-place)
- [ ] 両 textarea が空のとき Analyze は `disabled`
- [ ] verify_public_demo.py pass (`Mighty Skill-Bridge` / `Analyze` マーカー保持)

## 12. Implementation Prompt (LLM-ready)

```text
You are implementing WF-02 "Split Form" for Mighty Skill-Bridge, the closest to the current index.html.

Constraints: same as WF-01 (static/wireframes/wf-02.html, vanilla, no build, use /api/parse + /api/match).

Key differences vs WF-01:
- Two-column grid for desktop (≥ 901px), collapses to 1-column on mobile
- CTA is centered horizontally and visually de-emphasizes after first result
- Result band reveals in-place (no scrollIntoView)
- Reuse existing sample text loaders (loadSampleEngineer / loadSampleJob)

Acceptance: see docs/wireframes/WF-02_split_form.md §11. Do not touch root index.html.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mighty Skill-Bridge — WF-02</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;--c-border:#2A2D3E;
      --r-md:12px;--r-lg:20px;--s-3:16px;--s-4:24px;--s-5:40px;--fs-h2:22px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf02{display:grid;gap:var(--s-4);max-width:1280px;margin:0 auto;padding:var(--s-4)}
.wf02__grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--s-4)}
@media (max-width:900px){.wf02__grid{grid-template-columns:1fr}}
textarea{width:100%;box-sizing:border-box;background:var(--c-surface);color:var(--c-text);
         border:1px solid var(--c-border);border-radius:var(--r-md);padding:var(--s-3);min-height:340px}
.wf02__cta{justify-self:center;padding:var(--s-3) var(--s-5);background:var(--c-accent);
           color:var(--c-bg);border:0;border-radius:var(--r-lg);font-size:var(--fs-h2);font-weight:700}
.wf02__cta:disabled{opacity:.4}
.wf02__result[hidden]{display:none}
.wf02__result{display:grid;grid-template-columns:360px 1fr;gap:var(--s-4)}
@media (max-width:900px){.wf02__result{grid-template-columns:1fr}}
</style></head><body>
<main class="wf02">
  <h1>Mighty Skill-Bridge</h1>
  <div class="wf02__grid">
    <section><h2>経歴書</h2><textarea id="engineer"></textarea></section>
    <section><h2>案件票</h2><textarea id="job"></textarea></section>
  </div>
  <button class="wf02__cta" id="analyze" disabled>⚡ Analyze Fit</button>
  <section class="wf02__result" id="result" aria-live="polite" hidden></section>
</main>
<script>
const $=(s)=>document.querySelector(s);
function syncCta(){$("#analyze").disabled = !($("#engineer").value.trim() && $("#job").value.trim())}
["engineer","job"].forEach(id=>$("#"+id).addEventListener("input",syncCta));
async function parseDoc(text, t){const fd=new FormData();fd.append("text",text);fd.append("doc_type",t);
  const r=await fetch("/api/parse",{method:"POST",body:fd});return r.json()}
async function match(e,j){const r=await fetch("/api/match",{method:"POST",
  headers:{"content-type":"application/json"},
  body:JSON.stringify({engineer_content:e,job_content:j})});return r.json()}
$("#analyze").addEventListener("click",async ev=>{
  ev.currentTarget.disabled=true;ev.currentTarget.setAttribute("aria-busy","true");
  try{const [p1,p2]=await Promise.all([parseDoc($("#engineer").value,"engineer"),parseDoc($("#job").value,"job")]);
    const m=await match(p1.parsed_text||$("#engineer").value,p2.parsed_text||$("#job").value);
    const r=$("#result");r.hidden=false;
    r.innerHTML=`<div><h2>Score ${m.final_score}</h2><pre>${JSON.stringify(m.scores,null,2)}</pre></div>
                 <div><p>${m.summary}</p></div>`;
  }finally{ev.currentTarget.disabled=false;ev.currentTarget.removeAttribute("aria-busy")}});
</script></body></html>
```
