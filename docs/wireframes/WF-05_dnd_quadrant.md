# WF-05 · Drag & Drop Cards — 4 Quadrant Workspace

> Subtitle: Engineers / Jobs / Matches / Reports の 4 象限。カード DnD。
> 💡 Rationale: 中規模の人事チームが複数案件 × 複数候補を同時管理。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-05` |
| category | workspace / drag-and-drop |
| status | spec-ready (visual = Canva slide 6) |
| pick-when | 中規模 HR チーム、複数候補 × 複数案件並列、視覚的整理重視 |
| skip-when | 初回ユーザー、モバイル中心、単発 1 候補 |
| output target | `exports/wireframes/wf-05.html` |

## 2. ASCII Layout

```text
┌──────────────────────────── 1440 width ─────────────────────────────────────┐
│  Mighty Skill-Bridge Workspace                          [+ New] [User]      │
├─────────────────────────────────┬───────────────────────────────────────────┤
│  Engineers (drop zone)          │  Jobs (drop zone)                         │
│  [👤 Aさん 5y Python]            │  [📋 案件A Senior Python]                  │
│  [👤 Bさん 3y React]             │  [📋 案件B Frontend React]                 │
│  [👤 Cさん 8y Cloud]             │  [📋 案件C DevOps]                         │
│  [+ Add]                        │  [+ Add]                                  │
├─────────────────────────────────┼───────────────────────────────────────────┤
│  Matches (drop both → analyze)  │  Reports (export)                         │
│  ┌─────────────────────┐         │  [▾ 今週] [▾ 全期間]                       │
│  │ Aさん × 案件A  88   │         │  [📊 Score 分布グラフ]                     │
│  │ Bさん × 案件B  72   │         │  [📥 CSV] [📥 PDF]                         │
│  └─────────────────────┘         │                                           │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf05">
  <header><h1>Workspace</h1><button>+ New</button></header>
  <div class="wf05__quadrants">
    <section class="wf05__zone" data-zone="engineers" aria-label="Engineers"><h2>Engineers</h2>
      <ul class="wf05__cards"><!-- li.card draggable=true --></ul>
      <button data-act="add" data-kind="engineer">+ Add</button></section>
    <section class="wf05__zone" data-zone="jobs"><h2>Jobs</h2><ul class="wf05__cards"></ul>
      <button data-act="add" data-kind="job">+ Add</button></section>
    <section class="wf05__zone wf05__zone--drop" data-zone="matches"><h2>Matches</h2>
      <p class="wf05__hint">経歴 card と案件 card をここに drop → 自動分析</p>
      <ul class="wf05__matches"></ul></section>
    <section class="wf05__zone" data-zone="reports"><h2>Reports</h2>
      <select><option>今週</option><option>全期間</option></select>
      <canvas class="wf05__chart" width="320" height="200"></canvas>
      <button>📥 CSV</button> <button>📥 PDF</button></section>
  </div>
</main>
```

## 4. State Machine

```text
idle ── add card  ──> idle (card pushed to zone)
idle ── drag start ──> dragging (card .is-dragging)
dragging ── drop on matches ──> pending-pair (1 card so far)
pending-pair ── drop second ──> analyzing → match-loaded → idle
dragging ── drop elsewhere ──> idle (no-op)
```

## 5. Data Flow + API contract

- Add Engineer/Job: modal で textarea → `POST /api/parse` → ParsedProfile を client state へ。
- Matches zone に 2 cards drop で `POST /api/match` 自動発火 → match card render。
- Reports: client side aggregate (matches 配列から bin)、CSV/PDF は client export (Papaparse / jsPDF CDN 任意)。

## 6. Design Tokens (override)

```css
.wf05 { padding: var(--s-3); }
.wf05__quadrants { display: grid; grid-template-columns: 1fr 1fr;
                   grid-template-rows: 1fr 1fr; gap: var(--s-3); height: calc(100vh - 100px); }
.wf05__zone { background: var(--c-surface); border: 1px solid var(--c-border);
              border-radius: var(--r-lg); padding: var(--s-3); overflow-y: auto; }
.wf05__zone--drop.is-over { border-color: var(--c-accent); box-shadow: inset 0 0 0 2px var(--c-accent); }
.wf05__cards li { background: var(--c-bg); border: 1px solid var(--c-border);
                  padding: var(--s-2); border-radius: var(--r-md); margin-bottom: var(--s-2);
                  cursor: grab; }
.wf05__cards li.is-dragging { opacity: 0.5; cursor: grabbing; }
```

## 7. Interaction Spec

- HTML5 drag-and-drop API (`draggable="true"`, `dragstart`/`dragover`/`drop`).
- mobile: pointer events で fallback (long-press → drag) — out-of-scope の場合は desktop 専用と明記し mobile では reorder ボタン提供。
- 視覚 feedback: drop zone `dragover` で `.is-over` 付与。
- match card に Score gauge mini (24px)。

## 8. A11y

- DnD は keyboard 対応必須: 各 card に "Move to..." menu (Space で開く)。
- screen reader 用に `aria-grabbed` (deprecated だが widely supported) または `aria-describedby` で操作ヒント。
- mobile fallback の reorder ボタンは "Move up/down" `<button>`。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 900 | `grid-template-columns: 1fr; grid-template-rows: repeat(4, auto)` (縦積み)、DnD 無効 → tap to move menu |
| 901-1280 | 2x2 grid、card 大きめ |
| ≥ 1281 | 2x2 grid、各 zone 480px+、card 横スクロールなし |

## 10. Out of Scope

- DB 永続化 (sessionStorage のみ)
- 複数ユーザー collaboration (single-user only)
- realtime sync (no WebSocket)
- 高度な分析グラフ (canvas で score histogram のみ)

## 11. Acceptance Criteria

- [ ] desktop で engineer card と job card を Matches zone に drag&drop で配置 → 自動 /api/match → score 表示
- [ ] mobile では DnD 不可だが "Move to Matches" menu で同等操作可
- [ ] Add Engineer modal で /api/parse 呼び出し → card に Name + Years 表示
- [ ] Reports zone で score 分布 canvas が match 件数に応じて更新
- [ ] keyboard only で Move menu → Matches zone 配置完走
- [ ] verify_public_demo.py pass (root 触らない)

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-05 "DnD 4-Quadrant Workspace" for Mighty Skill-Bridge as exports/wireframes/wf-05.html.

Stack: vanilla HTML/JS, HTML5 drag-and-drop API. Use POST /api/parse on Add modal,
POST /api/match when 2 cards land in Matches zone.

UI: 2x2 grid (Engineers / Jobs / Matches / Reports). Cards draggable from Engineers/Jobs.
When both an engineer and job card are dropped in Matches, auto-analyze and render a match card.
Reports zone: client-side score histogram (canvas) + CSV/PDF export buttons (CDN optional).

Mobile (≤900): collapse to vertical stack, disable DnD, provide "Move to..." menu per card.

Acceptance: docs/wireframes/WF-05_dnd_quadrant.md §11. No build, no framework. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-05 Workspace</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;
      --c-border:#2A2D3E;--r-md:12px;--r-lg:20px;--s-2:8px;--s-3:16px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf05__quadrants{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;
                 gap:var(--s-3);padding:var(--s-3);height:100vh;box-sizing:border-box}
@media (max-width:900px){.wf05__quadrants{grid-template-columns:1fr;grid-template-rows:repeat(4,auto);height:auto}}
.wf05__zone{background:var(--c-surface);border:1px solid var(--c-border);
            border-radius:var(--r-lg);padding:var(--s-3);overflow-y:auto}
.wf05__zone.is-over{border-color:var(--c-accent)}
.wf05__cards{list-style:none;padding:0;margin:0}
.wf05__cards li{background:var(--c-bg);border:1px solid var(--c-border);
                padding:var(--s-2);border-radius:var(--r-md);margin-bottom:var(--s-2);cursor:grab}
button{background:var(--c-accent);color:var(--c-bg);border:0;border-radius:var(--r-md);padding:var(--s-2) var(--s-3);font-weight:700}
</style></head><body>
<main class="wf05__quadrants">
  <section class="wf05__zone" data-zone="engineers"><h2>Engineers</h2><ul class="wf05__cards" id="z-eng"></ul><button data-add="engineer">+ Add</button></section>
  <section class="wf05__zone" data-zone="jobs"><h2>Jobs</h2><ul class="wf05__cards" id="z-job"></ul><button data-add="job">+ Add</button></section>
  <section class="wf05__zone wf05__zone--drop" data-zone="matches"><h2>Matches</h2><p>2 cards をここに drop</p><ul class="wf05__cards" id="z-mat"></ul></section>
  <section class="wf05__zone" data-zone="reports"><h2>Reports</h2><canvas id="chart" width="320" height="160"></canvas></section>
</main>
<script>
const state={engineers:[],jobs:[],matches:[],pending:[]};
const $=s=>document.querySelector(s);
function renderCards(zone,arr){const ul=$("#"+zone);ul.innerHTML="";
  arr.forEach((it,i)=>{const li=document.createElement("li");li.draggable=true;li.dataset.kind=zone.slice(2);li.dataset.idx=i;
    li.textContent=it.label;li.addEventListener("dragstart",e=>e.dataTransfer.setData("text/plain",JSON.stringify({k:li.dataset.kind,i:li.dataset.idx})));ul.appendChild(li);});}
function drawChart(){const c=$("#chart").getContext("2d");c.clearRect(0,0,320,160);
  c.fillStyle="#00F0FF";state.matches.forEach((m,i)=>c.fillRect(i*24+10,160-(m.score*1.4),20,m.score*1.4));}
document.querySelectorAll("[data-add]").forEach(b=>b.addEventListener("click",async()=>{
  const t=prompt("テキストを貼り付け"); if(!t) return;
  const fd=new FormData();fd.append("text",t);fd.append("doc_type",b.dataset.add);
  await fetch("/api/parse",{method:"POST",body:fd});
  const arr=b.dataset.add==="engineer"?state.engineers:state.jobs;
  arr.push({label:t.slice(0,30)+"…",text:t});
  renderCards(b.dataset.add==="engineer"?"z-eng":"z-job",arr);}));
const drop=document.querySelector('[data-zone="matches"]');
drop.addEventListener("dragover",e=>{e.preventDefault();drop.classList.add("is-over")});
drop.addEventListener("dragleave",()=>drop.classList.remove("is-over"));
drop.addEventListener("drop",async e=>{e.preventDefault();drop.classList.remove("is-over");
  const d=JSON.parse(e.dataTransfer.getData("text/plain"));
  state.pending.push(d);
  if(state.pending.length===2){const eng=state.pending.find(x=>x.k==="eng"),job=state.pending.find(x=>x.k==="job");
    state.pending=[]; if(!eng||!job){alert("engineer と job 各 1 枚必要");return;}
    const engT=state.engineers[+eng.i].text, jobT=state.jobs[+job.i].text;
    const m=await (await fetch("/api/match",{method:"POST",headers:{"content-type":"application/json"},
      body:JSON.stringify({engineer_content:engT,job_content:jobT})})).json();
    state.matches.push({score:m.final_score, label:`${engT.slice(0,8)} × ${jobT.slice(0,8)} = ${m.final_score}`});
    renderCards("z-mat",state.matches.map(x=>({label:x.label}))); drawChart();}});
</script></body></html>
```
