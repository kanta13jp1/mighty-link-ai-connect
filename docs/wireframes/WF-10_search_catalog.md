# WF-10 · Search-First Catalog — Engineer/Job Library

> Subtitle: 検索バー + フィルタ → グリッドカード → 詳細モーダル。
> 💡 Rationale: 蓄積データが増えた後の "リクルーターの日常入口"。検索駆動。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-10` |
| category | search / catalog |
| status | spec-ready (visual = Canva slide 11) |
| pick-when | データ蓄積後の日常運用、検索駆動でアイテム探す |
| skip-when | 初期データ 0 (空状態)、単発分析 |
| output target | `exports/wireframes/wf-10.html` |

## 2. ASCII Layout

```text
┌─────────────────────────── 1280 width ──────────────────────────────────────┐
│  Catalog                                                          [User]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 [search box: Python AWS Senior]              [tab: Engineers | Jobs ▾]  │
│  Filters: [年数 ▾] [言語 ▾] [Updated ▾] [Score ≥ 70 ▾]                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Results 14 / 142  · sorted by Updated ↓                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │👤 Aさん 88   │ │👤 Bさん 72   │ │👤 Cさん 91   │ │👤 Dさん 67   │         │
│  │5y Python AWS │ │3y React TS   │ │8y Go Cloud   │ │4y Python ML  │         │
│  │Updated 5/24  │ │Updated 5/23  │ │Updated 5/22  │ │Updated 5/22  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘         │
│  ... (grid continues, infinite scroll)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ (click card → drawer modal: 全文 + 過去 match 履歴 + Re-analyze ボタン)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf10">
  <header><h1>Catalog</h1></header>
  <form class="wf10__search" role="search">
    <input type="search" id="q" placeholder="検索 (例: Python AWS Senior)" aria-label="search">
    <fieldset><legend>Tab</legend>
      <input type="radio" name="tab" id="tab-eng" value="engineers" checked>
      <label for="tab-eng">Engineers</label>
      <input type="radio" name="tab" id="tab-job" value="jobs">
      <label for="tab-job">Jobs</label></fieldset>
    <details class="wf10__filters"><summary>Filters</summary>
      <label>年数 <select id="f-years"><option value="">all</option><option>3+</option><option>5+</option><option>8+</option></select></label>
      <label>言語 <select id="f-lang"><option value="">all</option><option>Python</option><option>Go</option><option>React</option></select></label>
      <label>Score <input type="number" id="f-score" min="50" max="100" placeholder="≥ 70"></label>
    </details>
  </form>
  <p class="wf10__meta"><span id="count">--</span> / <span id="total">--</span></p>
  <ul class="wf10__grid" id="results"></ul>
  <dialog class="wf10__drawer" id="drawer"></dialog>
</main>
```

## 4. State Machine

```text
empty (no data)     ── seed / import ──> populated
populated ── search/filter change ──> filtering (client filter, no fetch)
filtering ── done                 ──> rendered (count updated)
card click             ──> drawer-open
drawer open ── Re-analyze ──> drawer-analyzing → drawer-done
```

## 5. Data Flow + API contract

- 初期 catalog データ: `sessionStorage` から復元、または `GET /api/audit/recent?limit=500` で過去 parse audit から集計 (client-side dedup)。
- search/filter は client side: 検索文字列を空白 token 化、各 token を card text に AND マッチ。
- card click drawer: 該当 entry 詳細 + `POST /api/match` で再評価可能 (job 側カードなら engineer 選択 modal、engineer 側カードなら逆)。

## 6. Design Tokens (override)

```css
.wf10__search { display: grid; grid-template-columns: 1fr auto auto;
                 gap: var(--s-3); padding: var(--s-3);
                 position: sticky; top: 0; background: var(--c-bg); z-index: 5; }
.wf10__search input[type="search"] { background: var(--c-surface); color: var(--c-text);
                                       border: 1px solid var(--c-border); border-radius: var(--r-md);
                                       padding: var(--s-3); font-size: var(--fs-body); }
.wf10__grid { list-style:none; padding: var(--s-3); margin: 0;
              display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
              gap: var(--s-3); }
.wf10__grid li { background: var(--c-surface); border: 1px solid var(--c-border);
                  border-radius: var(--r-md); padding: var(--s-3); cursor: pointer; }
.wf10__drawer { width: 90vw; max-width: 720px; background: var(--c-surface);
                color: var(--c-text); border: 1px solid var(--c-border);
                border-radius: var(--r-lg); padding: var(--s-4); }
```

## 7. Interaction Spec

- search input: 250ms debounce、空白 token AND マッチ。
- filter select change: 即時 filter 再適用。
- card click: `<dialog>` open、card data を埋め込む。
- drawer close: Esc / 外側クリック / "閉じる" ボタン。
- Infinite scroll: `IntersectionObserver` で末尾 sentinel 検知、+24 件追加 (client-paginated)。

## 8. A11y

- search form: `role="search"`、`<input type="search">`、`<label>` 必須。
- tab: `<input type="radio">` で keyboard 操作 (Arrow Key)。
- card: `<li>` 内に `<button>` で focusable、Enter で drawer open。
- `<dialog>` の native semantics で focus trap + restore 自動。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 600 | grid 1 列、search sticky-top |
| 601-900 | grid auto-fill 240px (2-3 列) |
| ≥ 901 | grid auto-fill 240px (4-5 列)、drawer 720px |

## 10. Out of Scope

- 検索バックエンド (Elasticsearch 等)、全 client filter
- ページネーション URL (infinite scroll のみ、ハッシュ復元なし)
- 編集機能 (read-only library、編集は WF-05/06/07 で)
- リアルタイム反映 (manual refresh)

## 11. Acceptance Criteria

- [ ] search box 入力で 250ms 後に grid filter
- [ ] Tab 切替 (Engineers / Jobs) でデータソース swap
- [ ] filter (年数 / 言語 / score) AND 合成、count が更新
- [ ] card クリックで `<dialog>` drawer open、Esc で閉じる
- [ ] 末尾スクロールで +24 件追加 (IntersectionObserver)
- [ ] mobile 1 列、search sticky-top
- [ ] keyboard で search → tab → filter → card → drawer 完走
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-10 "Search-First Catalog" for Mighty Skill-Bridge as exports/wireframes/wf-10.html.

Stack: vanilla HTML/JS, IntersectionObserver for infinite scroll, native <dialog> for drawer.

Data: load from sessionStorage (key "wf10_catalog") OR fetch GET /api/audit/recent?limit=500
and dedup parse audit events into engineer/job entries client-side. No backend search.

UI: sticky search bar (250ms debounce, AND token match), tab switcher (Engineers / Jobs),
collapsible filters (年数/言語/score). Auto-fill grid (minmax 240px). Card click opens drawer
with full text + "Re-analyze" button (calls POST /api/match against opposite-side selection).

Mobile: 1-col, sticky search. Acceptance: docs/wireframes/WF-10 §11. No build. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-10 Catalog</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;
      --c-border:#2A2D3E;--r-md:12px;--r-lg:20px;--s-3:16px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf10__search{position:sticky;top:0;background:var(--c-bg);display:grid;
              grid-template-columns:1fr auto auto;gap:var(--s-3);padding:var(--s-3);z-index:5}
input[type="search"]{background:var(--c-surface);color:var(--c-text);border:1px solid var(--c-border);
                     border-radius:var(--r-md);padding:var(--s-3);font:inherit}
.wf10__grid{list-style:none;padding:var(--s-3);margin:0;display:grid;
            grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:var(--s-3)}
.wf10__grid li{background:var(--c-surface);border:1px solid var(--c-border);
               border-radius:var(--r-md);padding:var(--s-3);cursor:pointer}
.wf10__drawer{width:90vw;max-width:720px;background:var(--c-surface);color:var(--c-text);
              border:1px solid var(--c-border);border-radius:var(--r-lg);padding:var(--s-3)}
</style></head><body>
<header style="padding:var(--s-3)"><h1>Catalog</h1></header>
<form class="wf10__search" role="search">
  <input type="search" id="q" placeholder="検索 (Python AWS Senior)">
  <fieldset><label><input type="radio" name="tab" value="engineers" checked> Engineers</label>
    <label><input type="radio" name="tab" value="jobs"> Jobs</label></fieldset>
  <details><summary>Filters</summary>
    <input type="number" id="minScore" placeholder="min score" min="50" max="100"></details>
</form>
<p style="padding:0 var(--s-3)"><span id="count">--</span></p>
<ul class="wf10__grid" id="grid"></ul>
<dialog class="wf10__drawer" id="drawer"></dialog>
<script>
const state={data:{engineers:[],jobs:[]},query:"",tab:"engineers",minScore:0,page:0,pageSize:24};
async function loadCatalog(){
  const cached=sessionStorage.getItem("wf10_catalog");
  if(cached){state.data=JSON.parse(cached); return}
  try{const audits=await (await fetch("/api/audit/recent?limit=500")).json();
    (audits.events||[]).forEach(e=>{
      if(e.type==="parse"&&e.payload?.doc_type==="engineer")
        state.data.engineers.push({name:e.payload?.parsed_summary?.slice(0,16)||"engineer",
          text:e.payload?.source_excerpt||"",score:0,updated:e.timestamp});
      if(e.type==="parse"&&e.payload?.doc_type==="job")
        state.data.jobs.push({name:e.payload?.parsed_summary?.slice(0,16)||"job",
          text:e.payload?.source_excerpt||"",score:0,updated:e.timestamp});});
    sessionStorage.setItem("wf10_catalog",JSON.stringify(state.data));
  }catch(e){console.warn("audit fetch failed",e)}
}
function render(){
  const all=state.data[state.tab]||[];
  const tokens=state.query.toLowerCase().split(/\s+/).filter(Boolean);
  const filt=all.filter(x=>{
    if(state.minScore && x.score<state.minScore) return false;
    return tokens.every(t=>(x.name+" "+x.text).toLowerCase().includes(t));});
  document.getElementById("count").textContent=`${filt.length} / ${all.length}`;
  const ul=document.getElementById("grid"); ul.innerHTML="";
  filt.slice(0,(state.page+1)*state.pageSize).forEach((x,i)=>{
    const li=document.createElement("li");
    li.innerHTML=`<strong>${x.name}</strong><br><small>${(x.text||"").slice(0,80)}</small>`;
    li.addEventListener("click",()=>{document.getElementById("drawer").innerHTML=
      `<h2>${x.name}</h2><p>${x.text||""}</p><button onclick="document.getElementById('drawer').close()">閉じる</button>`;
      document.getElementById("drawer").showModal();}); ul.appendChild(li);});
}
document.getElementById("q").addEventListener("input",e=>{clearTimeout(window.__t);
  window.__t=setTimeout(()=>{state.query=e.target.value;state.page=0;render()},250)});
document.querySelectorAll("input[name='tab']").forEach(r=>r.addEventListener("change",e=>{
  state.tab=e.target.value;state.page=0;render()}));
document.getElementById("minScore").addEventListener("change",e=>{
  state.minScore=+e.target.value||0; render()});
window.addEventListener("scroll",()=>{
  if(window.innerHeight+window.scrollY >= document.body.offsetHeight-200){state.page++; render()}});
loadCatalog().then(render);
</script></body></html>
```
