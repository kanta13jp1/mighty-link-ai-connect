# WF-07 · Comparison Table — Multi-candidate Matrix

> Subtitle: 候補 (rows) × 評価軸 (cols)。color-coded score。
> 💡 Rationale: 経営報告/最終決裁で最強。1 画面で 5-10 候補を比較できる。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-07` |
| category | comparison / data-grid |
| status | spec-ready (visual = Canva slide 8) |
| pick-when | 経営層への報告、最終 5-10 候補絞り込み |
| skip-when | 単発分析、入力 UI なし (前処理 WF と組み合わせ前提) |
| output target | `exports/wireframes/wf-07.html` |

## 2. ASCII Layout

```text
┌────────────────────────────── 1440 width ───────────────────────────────────────┐
│  Comparison · 案件: 株式会社X Senior Python              [Export CSV]            │
├─────────────┬─────────┬─────────┬─────────┬──────────────┬──────────────────────┤
│ 候補        │ Skill   │ Culture │ Growth  │ Performing   │ Final ▼              │
├─────────────┼─────────┼─────────┼─────────┼──────────────┼──────────────────────┤
│ Aさん       │  88 🟢  │  82 🟢  │  75 🟡  │  90 🟢       │  85 🟢               │
│ Bさん       │  72 🟡  │  90 🟢  │  88 🟢  │  70 🟡       │  80 🟢               │
│ Cさん       │  60 🔴  │  70 🟡  │  85 🟢  │  65 🟡       │  70 🟡               │
│ Dさん       │  95 🟢  │  60 🔴  │  70 🟡  │  88 🟢       │  78 🟡               │
│ Eさん       │  80 🟢  │  85 🟢  │  72 🟡  │  75 🟡       │  78 🟡               │
└─────────────┴─────────┴─────────┴─────────┴──────────────┴──────────────────────┘
                                     [+ Add Candidate]
```

## 3. Component Tree

```html
<main class="wf07">
  <header><h1>Comparison</h1>
    <p>案件: <strong id="job-title">--</strong></p>
    <button data-act="export-csv">Export CSV</button></header>
  <table class="wf07__matrix">
    <thead><tr><th scope="col">候補</th>
      <th scope="col" data-sort="skill">Skill</th>
      <th scope="col" data-sort="culture">Culture</th>
      <th scope="col" data-sort="growth">Growth</th>
      <th scope="col" data-sort="performing">Performing</th>
      <th scope="col" data-sort="final_score" aria-sort="descending">Final ▼</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <button data-act="add">+ Add Candidate</button>
</main>
```

## 4. State Machine

```text
empty ── set job + add candidate ──> rows = 1 (sorted by final)
rows  ── add candidate           ──> rows += 1 (re-sort)
rows  ── click column header     ──> resort by that column
rows  ── export CSV              ──> client download
```

## 5. Data Flow + API contract

- Job text を画面上部で 1 度入力 (modal or input row) → state.job_content。
- Add Candidate: 経歴 textarea → `POST /api/parse` (engineer) → `POST /api/match` ({engineer_content, job_content: state.job_content}) → row 追加。
- Sort: client side (`Array.sort`)、`aria-sort` 属性更新。

## 6. Design Tokens (override)

```css
.wf07__matrix { width: 100%; border-collapse: collapse; background: var(--c-surface); }
.wf07__matrix th, .wf07__matrix td { padding: var(--s-3); text-align: left;
                                       border-bottom: 1px solid var(--c-border); }
.wf07__matrix th { cursor: pointer; user-select: none; color: var(--c-text-sub); }
.wf07__matrix th[aria-sort] { color: var(--c-accent); }
.wf07__matrix td[data-band="high"] { background: rgba(57,255,20,0.12); color: var(--c-success); }
.wf07__matrix td[data-band="mid"]  { background: rgba(0,240,255,0.10); color: var(--c-accent); }
.wf07__matrix td[data-band="low"]  { background: rgba(255,51,102,0.10); color: var(--c-danger); }
.wf07__matrix tr:hover { background: rgba(255,255,255,0.04); }
```

## 7. Interaction Spec

- Column header click: toggle asc/desc、`aria-sort="ascending"`/`"descending"` 更新、他列の `aria-sort` 削除。
- Cell の色は score band (≥80 high / 65-79 mid / <65 low)。
- Export CSV: BOM 付き UTF-8 で `<job>_<timestamp>.csv` を `URL.createObjectURL` でダウンロード。
- Row click: drawer で詳細 (QA / roadmap / summary)。

## 8. A11y

- `<table>` semantic + `<th scope="col">` + `aria-sort` の正規利用。
- 色だけに頼らず band バッジ (🟢/🟡/🔴) を併記、screen reader 用 `aria-label="high score"`。
- keyboard: header `<button>` 化、Enter で sort。
- Row drawer は `<dialog>`、Esc で閉じる。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 700 | table を `<details>` per row に変換 (列ヘッダ → ラベル化) |
| 701-1100 | table 全 6 列、horizontal scroll 許容 |
| ≥ 1101 | table fixed columns、Sticky header (`position: sticky; top: 0`) |

## 10. Out of Scope

- 複数 job 同時比較 (1 job at a time)
- Backend persistence (client only)
- Pivot table 変換
- Chart 描画 (→ WF-08)

## 11. Acceptance Criteria

- [ ] 5 候補追加で table 5 行、Final 列 desc sort
- [ ] 各 score cell が band 色 (high/mid/low) で着色、絵文字バッジ併記
- [ ] 列ヘッダクリックで sort 切替、`aria-sort` が更新される
- [ ] Export CSV で UTF-8 BOM 付き CSV をダウンロード可
- [ ] mobile (≤700) で details 表示に縮退
- [ ] keyboard で全 sort/add/export 完走
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-07 "Comparison Table" for Mighty Skill-Bridge as exports/wireframes/wf-07.html.

Stack: vanilla HTML/JS. Use POST /api/parse + POST /api/match per Add Candidate.

UI: 6-column table (候補 / Skill / Culture / Growth / Performing / Final). Sortable headers
with aria-sort. Score band coloring + emoji badge. Job text input at top (1 job per session).
Add Candidate modal: paste engineer text → parse → match against current job → append row.
Export CSV: UTF-8 BOM, filename includes timestamp.

Mobile (≤700) collapses to <details> per row. Acceptance: docs/wireframes/WF-07 §11.
No backend changes, no build. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-07 Comparison</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-text-sub:#C5CAE0;
      --c-accent:#00F0FF;--c-success:#39FF14;--c-danger:#FF3366;--c-border:#2A2D3E;
      --r-md:12px;--s-3:16px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif;padding:var(--s-3)}
.wf07__matrix{width:100%;border-collapse:collapse;background:var(--c-surface);border-radius:var(--r-md);overflow:hidden}
.wf07__matrix th,.wf07__matrix td{padding:var(--s-3);text-align:left;border-bottom:1px solid var(--c-border)}
.wf07__matrix th{cursor:pointer;color:var(--c-text-sub);user-select:none;position:sticky;top:0;background:var(--c-surface)}
.wf07__matrix th[aria-sort]{color:var(--c-accent)}
.wf07__matrix td[data-band="high"]{background:rgba(57,255,20,.12);color:var(--c-success)}
.wf07__matrix td[data-band="mid"]{background:rgba(0,240,255,.10);color:var(--c-accent)}
.wf07__matrix td[data-band="low"]{background:rgba(255,51,102,.10);color:var(--c-danger)}
button{background:var(--c-accent);color:var(--c-bg);border:0;border-radius:var(--r-md);padding:8px 16px;font-weight:700;margin-top:var(--s-3)}
input{background:#0a0b12;color:var(--c-text);border:1px solid var(--c-border);border-radius:var(--r-md);padding:8px;font:inherit}
</style></head><body>
<h1>Comparison</h1>
<p>案件: <input id="job" placeholder="案件テキスト" size="60"></p>
<table class="wf07__matrix"><thead><tr>
  <th>候補</th><th data-key="skill">Skill</th><th data-key="culture">Culture</th>
  <th data-key="growth">Growth</th><th data-key="performing">Performing</th>
  <th data-key="final_score" aria-sort="descending">Final ▼</th></tr></thead>
<tbody id="rows"></tbody></table>
<button id="add">+ Add Candidate</button>
<button id="csv">Export CSV</button>
<script>
const state={rows:[],sortKey:"final_score",dir:-1};
function band(s){return s>=80?"high":s<65?"low":"mid"}
function badge(s){return s>=80?"🟢":s<65?"🔴":"🟡"}
function render(){state.rows.sort((a,b)=>(a[state.sortKey]-b[state.sortKey])*state.dir);
  document.getElementById("rows").innerHTML=state.rows.map(r=>
    `<tr><td>${r.name}</td>`+["skill","culture","growth","performing","final_score"].map(k=>
      `<td data-band="${band(r[k])}">${r[k]} ${badge(r[k])}</td>`).join("")+`</tr>`).join("");}
document.querySelectorAll("th[data-key]").forEach(th=>th.addEventListener("click",()=>{
  const k=th.dataset.key;
  if(state.sortKey===k){state.dir*=-1}else{state.sortKey=k;state.dir=-1}
  document.querySelectorAll("th[data-key]").forEach(x=>x.removeAttribute("aria-sort"));
  th.setAttribute("aria-sort",state.dir<0?"descending":"ascending"); render();}));
document.getElementById("add").addEventListener("click",async()=>{
  const eng=prompt("経歴書"); if(!eng) return;
  const job=document.getElementById("job").value.trim();
  if(!job){alert("先に案件を入力");return;}
  const m=await (await fetch("/api/match",{method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({engineer_content:eng,job_content:job})})).json();
  state.rows.push({name:eng.split("\n")[0].slice(0,16),...m.scores,final_score:m.final_score});
  render();});
document.getElementById("csv").addEventListener("click",()=>{
  const head="候補,Skill,Culture,Growth,Performing,Final\n";
  const body=state.rows.map(r=>[r.name,r.skill,r.culture,r.growth,r.performing,r.final_score].join(",")).join("\n");
  const blob=new Blob(["﻿"+head+body],{type:"text/csv"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download=`comparison_${Date.now()}.csv`; a.click();});
</script></body></html>
```
