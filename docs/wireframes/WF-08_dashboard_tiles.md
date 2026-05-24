# WF-08 · Dashboard Tiles — Exec Overview

> Subtitle: 6 タイル: 本日マッチ / Score 分布 / Skill Gap / Recent / Queue / Metrics。
> 💡 Rationale: 社長 / 経営層が一目で全体把握。週次レビューで使う。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-08` |
| category | dashboard / executive |
| status | spec-ready (visual = Canva slide 9) |
| pick-when | 社長 / 経営層、週次レビュー、KPI 一覧 |
| skip-when | 1 候補単発分析、入力 UI 必要 |
| output target | `exports/wireframes/wf-08.html` |

## 2. ASCII Layout

```text
┌─────────────────────────── 1440 width ────────────────────────────────────────┐
│  Mighty Skill-Bridge — Exec Dashboard          [今週 ▾] [全期間 ▾] [User]      │
├──────────────────┬──────────────────┬─────────────────────────────────────────┤
│ Tile 1           │ Tile 2           │ Tile 3                                  │
│ 本日マッチ        │ Score 分布        │ Skill Gap (top 5)                       │
│   34 件          │ [hist canvas]    │ ・Kubernetes                            │
│   (▲ +5)         │ avg 78.3          │ ・GoLang                                │
│                  │                  │ ・Terraform ... ※5 件                   │
├──────────────────┼──────────────────┼─────────────────────────────────────────┤
│ Tile 4           │ Tile 5           │ Tile 6                                  │
│ Recent Matches   │ Queue            │ API Metrics                             │
│ ・A × X    88    │ ・3 件 待機       │ 24h calls: 142                          │
│ ・B × Y    72    │ ・1 件 evaluating│ p95 latency: 1.2s                       │
│ ・C × Z    85    │                  │ fallback rate: 12%                      │
└──────────────────┴──────────────────┴─────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf08">
  <header><h1>Exec Dashboard</h1>
    <select aria-label="期間"><option>今週</option><option>全期間</option></select></header>
  <section class="wf08__grid">
    <article class="wf08__tile" data-tile="today-matches"><h2>本日マッチ</h2>
      <p class="wf08__big" data-val="0">--</p><p class="wf08__delta"></p></article>
    <article class="wf08__tile" data-tile="score-dist"><h2>Score 分布</h2>
      <canvas width="320" height="160"></canvas><p>avg <span class="avg">--</span></p></article>
    <article class="wf08__tile" data-tile="skill-gap"><h2>Skill Gap</h2><ol></ol></article>
    <article class="wf08__tile" data-tile="recent"><h2>Recent Matches</h2><ul></ul></article>
    <article class="wf08__tile" data-tile="queue"><h2>Queue</h2><ul></ul></article>
    <article class="wf08__tile" data-tile="api-metrics"><h2>API Metrics</h2>
      <dl><dt>24h calls</dt><dd class="calls"></dd>
          <dt>p95 latency</dt><dd class="p95"></dd>
          <dt>fallback rate</dt><dd class="fb"></dd></dl></article>
  </section>
</main>
```

## 4. State Machine

```text
init    ── fetch all 6 sources ──> loading (6 spinners)
loading ── all 200            ──> ready (all tiles populated)
loading ── partial 200        ──> ready-partial (tile-level error message in failing tiles)
ready   ── change period      ──> loading (re-fetch all 6)
```

## 5. Data Flow + API contract

各 tile 別 fetch (並列):

- today-matches: client-side count from `/api/audit/recent` (filter today)
- score-dist: 同上 + histogram canvas
- skill-gap: `/api/audit/recent` の jobs 側 unmatched skills 集計 (client)
- recent: `/api/audit/recent?limit=5`
- queue: client state (本 demo は constant、将来 pipeline backend と接続)
- api-metrics: `/api/admin/usage` から calls / latency / fallback_rate

(現状 backend に `/api/dashboard/summary` がないため client aggregate で構成。将来 single endpoint 追加余地として docs に記載。)

## 6. Design Tokens (override)

```css
.wf08__grid { display: grid; grid-template-columns: repeat(3, 1fr);
              grid-template-rows: repeat(2, 1fr); gap: var(--s-3); padding: var(--s-3); }
.wf08__tile { background: var(--c-surface); border: 1px solid var(--c-border);
              border-radius: var(--r-lg); padding: var(--s-4);
              display: grid; gap: var(--s-2); }
.wf08__tile h2 { font-size: var(--fs-h2); color: var(--c-text-sub); margin: 0; }
.wf08__big { font-size: 48px; font-weight: 800; color: var(--c-accent); margin: 0; }
.wf08__delta { color: var(--c-success); font-size: var(--fs-sm); }
.wf08__delta[data-dir="down"] { color: var(--c-danger); }
```

## 7. Interaction Spec

- 期間 select 変更で全 tile 再 fetch (loading state)。
- tile クリックで該当ソース drawer (例: Recent → 全件 list)。
- canvas histogram は score を 10 bin に。
- error tile は inline "再読込" ボタン。

## 8. A11y

- `<article>` per tile、`<h2>` で landmark 構造。
- `<dl>` for API metrics (definition list, semantic)。
- color に頼らず delta は ▲▼ 記号 + 値で示す。
- canvas には `aria-label="Score distribution, mean 78.3"` を付与、データテーブル alt を `<details>` 内に。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 800 | 1 列 (grid-template-columns: 1fr)、tile order 上から重要度順 |
| 801-1280 | 2 列 (3x2 → 2x3) |
| ≥ 1281 | 3x2 (原案) |

## 10. Out of Scope

- 入力 UI (この WF は read-only ダッシュボード、入力は WF-01..04 と組み合わせ)
- リアルタイム push (manual refresh / interval polling only)
- カスタム tile (固定 6 tiles)
- export CSV (→ WF-07)

## 11. Acceptance Criteria

- [ ] 6 tile が初期表示後 5s 以内に全て populated
- [ ] /api/admin/usage が 200 を返さない場合、API Metrics tile に "再読込" ボタン表示
- [ ] 期間切替で全 tile が再 fetch (loading state visible)
- [ ] mobile 1 列、tablet 2 列、desktop 3 列の grid に切り替わる
- [ ] canvas histogram の代わりに `<details>` で score テーブル alt を提供
- [ ] keyboard で 期間 select / tile drawer / 再読込 を完走
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-08 "Exec Dashboard Tiles" for Mighty Skill-Bridge as exports/wireframes/wf-08.html.

Stack: vanilla HTML/JS, Canvas 2D for histogram. Use GET /api/audit/recent + GET /api/admin/usage.

UI: 3x2 grid of 6 tiles (本日マッチ / Score 分布 / Skill Gap / Recent / Queue / API Metrics).
Period select at top (今週 / 全期間). Each tile fetches independently and renders loading / error
inline. Canvas histogram with aria-label + <details> data table alternative.

Acceptance: docs/wireframes/WF-08_dashboard_tiles.md §11. No backend changes, no build. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-08 Dashboard</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-text-sub:#C5CAE0;
      --c-accent:#00F0FF;--c-success:#39FF14;--c-danger:#FF3366;--c-border:#2A2D3E;
      --r-lg:20px;--s-2:8px;--s-3:16px;--s-4:24px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf08__grid{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(2,1fr);
            gap:var(--s-3);padding:var(--s-3);min-height:90vh}
@media (max-width:1280px){.wf08__grid{grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(3,1fr)}}
@media (max-width:800px){.wf08__grid{grid-template-columns:1fr;grid-template-rows:repeat(6,auto)}}
.wf08__tile{background:var(--c-surface);border:1px solid var(--c-border);
            border-radius:var(--r-lg);padding:var(--s-4);display:grid;gap:var(--s-2)}
.wf08__tile h2{margin:0;color:var(--c-text-sub);font-size:20px}
.wf08__big{font-size:48px;font-weight:800;color:var(--c-accent);margin:0}
canvas{width:100%;height:160px;background:#0a0b12;border-radius:8px}
</style></head><body>
<header style="padding:var(--s-3)"><h1>Exec Dashboard</h1></header>
<section class="wf08__grid" id="grid">
  <article class="wf08__tile" data-tile="today"><h2>本日マッチ</h2><p class="wf08__big" id="today-val">--</p></article>
  <article class="wf08__tile" data-tile="dist"><h2>Score 分布</h2><canvas id="hist"></canvas><p>avg <span id="avg">--</span></p></article>
  <article class="wf08__tile" data-tile="gap"><h2>Skill Gap</h2><ol id="gap"></ol></article>
  <article class="wf08__tile" data-tile="recent"><h2>Recent</h2><ul id="recent"></ul></article>
  <article class="wf08__tile" data-tile="queue"><h2>Queue</h2><ul id="queue"><li>(client state, future backend)</li></ul></article>
  <article class="wf08__tile" data-tile="api"><h2>API Metrics</h2><dl id="api"></dl></article>
</section>
<script>
async function loadAll(){
  try{const audits=await (await fetch("/api/audit/recent?limit=50")).json();
    const matches=(audits.events||[]).filter(e=>e.type==="match");
    document.getElementById("today-val").textContent=matches.length;
    const scores=matches.map(m=>m.payload?.final_score||0).filter(Boolean);
    const avg=scores.reduce((a,b)=>a+b,0)/(scores.length||1);
    document.getElementById("avg").textContent=avg.toFixed(1);
    const c=document.getElementById("hist").getContext("2d"); c.fillStyle="#00F0FF";
    const w=document.getElementById("hist").width=document.getElementById("hist").clientWidth;
    const bins=Array(10).fill(0); scores.forEach(s=>bins[Math.min(9,Math.floor(s/10))]++);
    const max=Math.max(...bins,1); bins.forEach((v,i)=>c.fillRect(i*w/10+2,160-v/max*150,w/10-4,v/max*150));
    document.getElementById("recent").innerHTML=matches.slice(0,5).map(m=>`<li>${m.payload?.final_score||"?"}</li>`).join("");
  }catch(e){console.error(e)}
  try{const u=await (await fetch("/api/admin/usage")).json();
    document.getElementById("api").innerHTML=`<dt>24h calls</dt><dd>${u.calls||0}</dd>
      <dt>fallback rate</dt><dd>${(u.fallback_rate||0)*100|0}%</dd>`;
  }catch(e){document.getElementById("api").innerHTML="<dt>error</dt><dd>再読込</dd>"}
}
loadAll();
</script></body></html>
```
