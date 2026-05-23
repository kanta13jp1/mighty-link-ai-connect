# WF-03 · Step Wizard — 4-step Progress Flow

> Subtitle: 経歴 → 案件 → 確認 → 結果。1 ステップずつ集中。
> 💡 Rationale: 初めて使う社内人事担当が迷わない。各ステップで Help が出せる。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-03` |
| category | onboarding / wizard |
| status | spec-ready (visual = Canva slide 4) |
| pick-when | 初回ユーザー多い、social 内部展開、help/tooltip 充実したい |
| skip-when | 慣れたヘビーユーザーが速度優先 |
| output target | `static/wireframes/wf-03.html` |

## 2. ASCII Layout

```text
┌──────────────────────────── 960 width ───────────────────────────────┐
│  Mighty Skill-Bridge                                       [Help ?] │
├──────────────────────────────────────────────────────────────────────┤
│  ●━━━━━━━━●━━━━━━━━○━━━━━━━━○        (progress bar 4 steps)         │
│  Step 1   Step 2   Step 3   Step 4                                  │
│  経歴入力  案件入力  確認     結果                                    │
├──────────────────────────────────────────────────────────────────────┤
│  [Step Card]                                                         │
│   Step 2 / 4 ─ 案件票を入力                                          │
│   [textarea 12 rows]                                                 │
│   ヒント: PDF / 画像も OK (Gemini multi-modal)                       │
│   [📎 Upload] [Load Sample]                                          │
│                                                                      │
│   [← Back]                              [Next →]                     │
└──────────────────────────────────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf03">
  <header><h1>Mighty Skill-Bridge</h1><button aria-label="help">Help ?</button></header>
  <ol class="wf03__steps" role="list">
    <li aria-current="step" data-step="1">経歴入力</li>
    <li data-step="2">案件入力</li>
    <li data-step="3">確認</li>
    <li data-step="4">結果</li>
  </ol>
  <section class="wf03__card" aria-live="polite">
    <h2><span class="step-num">Step 2 / 4</span> — 案件票を入力</h2>
    <!-- per-step body slot, swapped client-side -->
    <textarea id="step-body"></textarea>
    <p class="wf03__hint">ヒント: PDF / 画像も OK</p>
  </section>
  <nav class="wf03__nav">
    <button data-act="back" disabled>← Back</button>
    <button data-act="next">Next →</button>
  </nav>
</main>
```

## 4. State Machine

```text
step1 ── next ──> step2 ── next ──> step3 ── analyze ──> step3-loading
step3-loading ── 200 ──> step4(results)
step3-loading ── error ──> step3(error toast)
any-step ── back ──> previous-step (preserve data)
```

State variables: `currentStep: 1..4`, `data: {engineer: "", job: "", profile1, profile2, match}`.

## 5. Data Flow + API contract

- Step 1 完了時 (Next クリック): `POST /api/parse` (`doc_type=engineer`) → `data.profile1`
- Step 2 完了時: `POST /api/parse` (`doc_type=job`) → `data.profile2`
- Step 3 で "Analyze" CTA → `POST /api/match` → `data.match` → Step 4 へ遷移
- 各 fetch エラー時は同 step に留まり、`aria-live` で読み上げ

(parse を step 区切りで行うことで step3 までに client が profile を確定できる。)

## 6. Design Tokens (override)

```css
.wf03 { max-width: 960px; margin: 0 auto; padding: var(--s-4); }
.wf03__steps { display:flex; gap:var(--s-4); list-style:none; padding:0; counter-reset:step; }
.wf03__steps li { flex:1; text-align:center; padding-bottom:var(--s-2);
                   border-bottom: 3px solid var(--c-border); color: var(--c-text-sub); }
.wf03__steps li[aria-current="step"] { border-bottom-color: var(--c-accent);
                                       color: var(--c-accent); font-weight:700; }
.wf03__card { background: var(--c-surface); border: 1px solid var(--c-border);
              border-radius: var(--r-lg); padding: var(--s-5); margin-top: var(--s-4); }
.wf03__nav { display:flex; justify-content:space-between; margin-top:var(--s-4); }
.wf03__nav button[data-act="next"] { background: var(--c-accent); color: var(--c-bg);
                                      padding: var(--s-3) var(--s-4); border-radius: var(--r-md); }
```

## 7. Interaction Spec

- Next ボタン: 当 step の API 完了まで `aria-busy="true"` + disabled。
- Back: data 保持、API call なし。
- step 1/2 で input 空のときは Next disabled。
- Step indicator は clickable: 既到達 step (`data-reached`) のみクリック許可。

## 8. A11y

- `<ol>` + `aria-current="step"` で screen reader が「Step 2 of 4, current」と読む。
- Help button は modal trigger (modal は `<dialog>` か role=dialog)、Esc で閉じる。
- Live announce: 「Step 3 のロード中」「結果が表示されました」を `wf03__card` の `aria-live="polite"` で。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 600 | step indicator 横スクロール (overflow-x: auto)、Back/Next は full-width stack |
| 601-960 | indicator 4 等分、card padding 縮小 |
| ≥ 961 | indicator 4 等分、card padding 40px |

## 10. Out of Scope

- 複数案件パイプライン (→ WF-06)
- 並列 multi-tab (→ WF-05)
- live preview (→ WF-09)

## 11. Acceptance Criteria

- [ ] step 1 → 2 → 3 → 4 の遷移で前 step データが保持される
- [ ] Step 3 で Analyze → Step 4 に遷移、戻ると Step 4 → Step 3 に巻き戻る
- [ ] keyboard only で全 step 完走可能
- [ ] step indicator のクリックで前到達 step に戻れる、未到達 step はクリック不可
- [ ] mobile 375 で step indicator 横スクロール表示
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-03 "Step Wizard" for Mighty Skill-Bridge as static/wireframes/wf-03.html.

Stack: vanilla HTML/JS, no build. Use POST /api/parse per step (engineer at step1→2, job at step2→3)
and POST /api/match at step3→4.

State: currentStep (1..4), persisted client-only object `data`. Back navigation must preserve input.

UI: 4-step progress indicator at top (aria-current="step"), single card body that swaps per step,
Back/Next nav at bottom. Help button opens <dialog>.

Acceptance: docs/wireframes/WF-03_step_wizard.md §11. Tokens: docs/wireframes/README.md §Design Tokens.

Output: complete single HTML file. Do not modify root index.html or src/index.html.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-03 Step Wizard</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-text-sub:#C5CAE0;
      --c-accent:#00F0FF;--c-border:#2A2D3E;--r-md:12px;--r-lg:20px;
      --s-2:8px;--s-3:16px;--s-4:24px;--s-5:40px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf03{max-width:960px;margin:0 auto;padding:var(--s-4)}
.wf03__steps{display:flex;gap:var(--s-4);list-style:none;padding:0}
.wf03__steps li{flex:1;text-align:center;padding-bottom:var(--s-2);
                border-bottom:3px solid var(--c-border);color:var(--c-text-sub)}
.wf03__steps li[aria-current="step"]{border-bottom-color:var(--c-accent);color:var(--c-accent);font-weight:700}
.wf03__card{background:var(--c-surface);border:1px solid var(--c-border);
            border-radius:var(--r-lg);padding:var(--s-5);margin-top:var(--s-4)}
textarea{width:100%;min-height:240px;background:#0a0b12;color:var(--c-text);
         border:1px solid var(--c-border);border-radius:var(--r-md);padding:var(--s-3);box-sizing:border-box}
.wf03__nav{display:flex;justify-content:space-between;margin-top:var(--s-4)}
.wf03__nav button{background:var(--c-surface);color:var(--c-text);border:1px solid var(--c-border);
                  padding:var(--s-3) var(--s-4);border-radius:var(--r-md);cursor:pointer}
.wf03__nav button[data-act="next"]{background:var(--c-accent);color:var(--c-bg);border:0}
</style></head><body>
<main class="wf03">
  <ol class="wf03__steps">
    <li data-step="1" aria-current="step">経歴入力</li>
    <li data-step="2">案件入力</li><li data-step="3">確認</li><li data-step="4">結果</li>
  </ol>
  <section class="wf03__card" id="card" aria-live="polite"></section>
  <nav class="wf03__nav"><button data-act="back" disabled>← Back</button>
    <button data-act="next">Next →</button></nav>
</main>
<script>
const state={step:1, data:{engineer:"", job:"", profile1:null, profile2:null, match:null}};
const $=s=>document.querySelector(s);
const STEPS={1:{title:"Step 1 / 4 — 経歴書を貼り付け",input:"engineer"},
             2:{title:"Step 2 / 4 — 案件票を貼り付け",input:"job"},
             3:{title:"Step 3 / 4 — 内容を確認",input:null},
             4:{title:"Step 4 / 4 — 結果",input:null}};
function render(){
  const s=STEPS[state.step], c=$("#card");
  c.innerHTML=`<h2>${s.title}</h2>`+
    (s.input ? `<textarea id="ta">${state.data[s.input]||""}</textarea>` :
     state.step===3 ? `<p>経歴: ${state.data.engineer.slice(0,80)}…<br>案件: ${state.data.job.slice(0,80)}…</p>
                       <button id="analyze">⚡ Analyze Fit</button>` :
     `<h3>Score ${state.data.match?.final_score}</h3>
      <pre>${JSON.stringify(state.data.match?.scores,null,2)}</pre>
      <p>${state.data.match?.summary||""}</p>`);
  document.querySelectorAll(".wf03__steps li").forEach(li=>{
    const n=+li.dataset.step;
    li.toggleAttribute("aria-current",n===state.step);});
  $('button[data-act="back"]').disabled = state.step===1;
  $('button[data-act="next"]').hidden = state.step===4;
  $('button[data-act="next"]').textContent = state.step===3 ? "結果へ →" : "Next →";
  if(state.step===3) $("#analyze")?.addEventListener("click", analyze);
}
async function parseDoc(text,t){const fd=new FormData();fd.append("text",text);fd.append("doc_type",t);
  return (await fetch("/api/parse",{method:"POST",body:fd})).json()}
async function analyze(){state.data.match=await (await fetch("/api/match",{method:"POST",
  headers:{"content-type":"application/json"},
  body:JSON.stringify({engineer_content:state.data.engineer,job_content:state.data.job})})).json();
  state.step=4; render();}
$('button[data-act="next"]').addEventListener("click",async ()=>{
  const s=STEPS[state.step]; if(s.input){state.data[s.input]=$("#ta").value;
    const prof=await parseDoc(state.data[s.input], s.input); state.data["profile"+state.step]=prof;}
  state.step++; render();});
$('button[data-act="back"]').addEventListener("click",()=>{state.step--; render();});
render();
</script></body></html>
```
