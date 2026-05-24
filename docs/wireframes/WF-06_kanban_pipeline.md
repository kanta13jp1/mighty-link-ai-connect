# WF-06 · Pipeline Board — Kanban for Recruiters

> Subtitle: 候補 → 評価中 → 推薦 → 配属済。Score badge 付きカード。
> 💡 Rationale: リクルーター業務の標準ビュー。複数案件並列追跡しやすい。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-06` |
| category | kanban / pipeline |
| status | spec-ready (visual = Canva slide 7) |
| pick-when | リクルーター日常運用、進捗状態追跡が中心 |
| skip-when | 単発分析、初回ユーザー、スマホ中心 |
| output target | `exports/wireframes/wf-06.html` |

## 2. ASCII Layout

```text
┌──────────────────────────── 1440 width ──────────────────────────────────────┐
│  Pipeline                                  [+ Add Candidate]  [▾ filters]    │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────────┤
│ 候補 (4)     │ 評価中 (2)   │ 推薦 (3)     │ 配属済 (1)   │                  │
│ ─────────    │ ─────────    │ ─────────    │ ─────────    │                  │
│ [👤 Aさん 88]│ [👤 Dさん 72]│ [👤 Gさん 91]│ [👤 Jさん 95]│                  │
│ [👤 Bさん 65]│ [👤 Eさん 80]│ [👤 Hさん 84]│              │                  │
│ [👤 Cさん 77]│              │ [👤 Iさん 70]│              │                  │
│ [👤 Fさん 92]│              │              │              │                  │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────────┘
```

Card mini layout:

```text
┌──────────────────────────┐
│ 👤 山田太郎    [88]      │
│ Senior Python · 8y       │
│ 案件: 株式会社X          │
│ Updated: 2026-05-24      │
└──────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf06">
  <header><h1>Pipeline</h1>
    <button data-act="add">+ Add Candidate</button>
    <details><summary>Filters</summary>...</details></header>
  <div class="wf06__columns">
    <section class="wf06__col" data-status="candidate"><h2>候補</h2>
      <ol class="wf06__cards"></ol></section>
    <section class="wf06__col" data-status="evaluating"><h2>評価中</h2>
      <ol class="wf06__cards"></ol></section>
    <section class="wf06__col" data-status="recommended"><h2>推薦</h2>
      <ol class="wf06__cards"></ol></section>
    <section class="wf06__col" data-status="placed"><h2>配属済</h2>
      <ol class="wf06__cards"></ol></section>
  </div>
</main>
<template id="card-tpl">
  <li class="wf06__card" draggable="true">
    <header><strong class="name"></strong><span class="score"></span></header>
    <p class="meta"></p><time class="upd"></time></li>
</template>
```

## 4. State Machine

```text
empty ── add candidate ──> candidate column has 1+
column-X ── drag to column-Y ──> persist new status (client state + optional PATCH)
recommended ── drag to placed ──> celebrate animation
```

## 5. Data Flow + API contract

- Add Candidate: modal で経歴 textarea + 案件選択 → `POST /api/parse` (engineer) → `POST /api/match` (job は既存 jobs から選択) → score を card に attach、候補 column に配置。
- Drag 状態変更: client only (no backend status field in current API)。将来 backend 追加余地として `PATCH /api/candidates/{id}` を docs に予約。
- Filters: client-side filter (score range / 案件 / 更新日)。

## 6. Design Tokens (override)

```css
.wf06__columns { display: grid; grid-template-columns: repeat(4, 1fr);
                  gap: var(--s-3); padding: var(--s-3); height: calc(100vh - 80px); }
.wf06__col { background: var(--c-surface); border: 1px solid var(--c-border);
              border-radius: var(--r-lg); padding: var(--s-3); overflow-y: auto; }
.wf06__col h2 { font-size: var(--fs-h2); margin: 0 0 var(--s-3); }
.wf06__card { background: var(--c-bg); border: 1px solid var(--c-border);
               border-radius: var(--r-md); padding: var(--s-3); margin-bottom: var(--s-2);
               cursor: grab; }
.wf06__card .score { float: right; color: var(--c-accent); font-weight: 700; }
.wf06__card[data-score-band="high"] { border-left: 4px solid var(--c-success); }
.wf06__card[data-score-band="mid"]  { border-left: 4px solid var(--c-accent); }
.wf06__card[data-score-band="low"]  { border-left: 4px solid var(--c-danger); }
```

## 7. Interaction Spec

- Drag: HTML5 DnD、`dragover` で hover column に `.is-over` 付与。
- Drop: column 内に append、card の `dataset.status` 更新、card の DOM order を上端に。
- Filter: form-level `<details>` 内に input/select、変更時に hidden 属性で非表示制御。
- Card click: 右側 drawer (sliding panel) で詳細表示 (`<dialog>` フルスクリーン非モーダル相当)。

## 8. A11y

- Drag 代替: card に "Move to..." ボタン (Space で開く select)。
- `<ol>` で順序読み上げ、 column heading は `<h2>`。
- Card は `role="article"`、score は `<span aria-label="Score 88 of 100">`。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 800 | columns 横スクロール (overflow-x: auto, column 280px min)、touch swipe で移動 |
| 801-1280 | 4 列等幅縮小、card padding 縮小 |
| ≥ 1281 | 4 列 + drawer overlay |

## 10. Out of Scope

- Multi-board (1 board only)
- Backend persistence (client-only state, sessionStorage 保存可)
- Realtime collab
- Score 自動再計算 (固定 snapshot)

## 11. Acceptance Criteria

- [ ] 4 列が常に表示され、各列にカード追加可
- [ ] Drag&Drop で card が column 間移動、status 更新
- [ ] Add Candidate で /api/parse + /api/match が呼ばれ、score バンド色が付与される
- [ ] Filter で score < 70 を非表示にできる
- [ ] mobile で横スクロール、各 column タッチで縦展開
- [ ] keyboard only でカード移動可能 (Move menu)
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-06 "Pipeline Board" for Mighty Skill-Bridge as exports/wireframes/wf-06.html.

Stack: vanilla HTML/JS, HTML5 DnD. Use POST /api/parse + POST /api/match on Add Candidate.

UI: 4 columns (候補 / 評価中 / 推薦 / 配属済). Cards drag between columns. Score band coloring:
high (≥80, green), mid (65-79, blue), low (<65, red). Filter <details> with score-range slider.

Acceptance: docs/wireframes/WF-06_kanban_pipeline.md §11. Mobile uses horizontal scroll on columns.
No backend status field exists - manage status client-side. No build, no framework. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-06 Pipeline</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;
      --c-success:#39FF14;--c-danger:#FF3366;--c-border:#2A2D3E;--r-md:12px;--r-lg:20px;--s-2:8px;--s-3:16px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf06__columns{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--s-3);
                padding:var(--s-3);height:100vh;box-sizing:border-box;overflow-x:auto}
@media (max-width:800px){.wf06__columns{grid-auto-columns:280px;grid-template-columns:none;grid-auto-flow:column}}
.wf06__col{background:var(--c-surface);border:1px solid var(--c-border);
            border-radius:var(--r-lg);padding:var(--s-3);overflow-y:auto;min-width:0}
.wf06__col.is-over{border-color:var(--c-accent)}
.wf06__cards{list-style:none;padding:0;margin:0}
.wf06__card{background:var(--c-bg);border:1px solid var(--c-border);border-radius:var(--r-md);
             padding:var(--s-3);margin-bottom:var(--s-2);cursor:grab;display:flex;justify-content:space-between;gap:var(--s-2)}
.wf06__card .score{color:var(--c-accent);font-weight:700}
.wf06__card[data-band="high"]{border-left:4px solid var(--c-success)}
.wf06__card[data-band="low"]{border-left:4px solid var(--c-danger)}
button{background:var(--c-accent);color:var(--c-bg);border:0;border-radius:var(--r-md);padding:var(--s-2) var(--s-3);font-weight:700}
header{padding:var(--s-3)}
</style></head><body>
<header><h1>Pipeline</h1><button id="add">+ Add Candidate</button></header>
<main class="wf06__columns" id="board">
  <section class="wf06__col" data-status="candidate"><h2>候補</h2><ol class="wf06__cards"></ol></section>
  <section class="wf06__col" data-status="evaluating"><h2>評価中</h2><ol class="wf06__cards"></ol></section>
  <section class="wf06__col" data-status="recommended"><h2>推薦</h2><ol class="wf06__cards"></ol></section>
  <section class="wf06__col" data-status="placed"><h2>配属済</h2><ol class="wf06__cards"></ol></section>
</main>
<script>
function band(s){return s>=80?"high":s<65?"low":"mid"}
function makeCard(c){const li=document.createElement("li");li.className="wf06__card";li.draggable=true;
  li.dataset.band=band(c.score);
  li.innerHTML=`<div><strong>${c.name}</strong><br><small>${c.meta}</small></div><span class="score">${c.score}</span>`;
  li.addEventListener("dragstart",e=>{e.dataTransfer.setData("text/plain",JSON.stringify(c));li.remove();});
  return li;}
document.querySelectorAll(".wf06__col").forEach(col=>{
  col.addEventListener("dragover",e=>{e.preventDefault();col.classList.add("is-over")});
  col.addEventListener("dragleave",()=>col.classList.remove("is-over"));
  col.addEventListener("drop",e=>{e.preventDefault();col.classList.remove("is-over");
    const c=JSON.parse(e.dataTransfer.getData("text/plain")); c.status=col.dataset.status;
    col.querySelector(".wf06__cards").appendChild(makeCard(c));});
});
document.getElementById("add").addEventListener("click",async()=>{
  const eng=prompt("経歴書テキスト"); if(!eng) return;
  const job=prompt("案件票テキスト"); if(!job) return;
  const fd=new FormData();fd.append("text",eng);fd.append("doc_type","engineer");
  await fetch("/api/parse",{method:"POST",body:fd});
  const fd2=new FormData();fd2.append("text",job);fd2.append("doc_type","job");
  await fetch("/api/parse",{method:"POST",body:fd2});
  const m=await (await fetch("/api/match",{method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({engineer_content:eng,job_content:job})})).json();
  const c={name:eng.split("\n")[0].slice(0,16),meta:job.split("\n")[0].slice(0,30),score:m.final_score,status:"candidate"};
  document.querySelector('[data-status="candidate"] .wf06__cards').appendChild(makeCard(c));
});
</script></body></html>
```
