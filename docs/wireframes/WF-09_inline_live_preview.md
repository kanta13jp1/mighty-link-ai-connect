# WF-09 · Inline Preview — Live Suggestions

> Subtitle: 入力中に右パネルへリアルタイム fit / 候補をストリーミング表示。
> 💡 Rationale: AI ライブ感を最大化。社長デモで「打ちながら結果が変わる」を見せる。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-09` |
| category | live-preview / split |
| status | spec-ready (visual = Canva slide 10) |
| pick-when | 社長デモ専用、AI ライブ感最大化、入力中に意思決定したい |
| skip-when | API 課金重い (debounce 必須)、本番運用 (quota 浪費リスク) |
| output target | `exports/wireframes/wf-09.html` |

## 2. ASCII Layout

```text
┌────────────────────────────── 1280 width ──────────────────────────────────┐
│  Live Preview                                          [▶ Demo Recording] │
├────────────────────────────────────────┬───────────────────────────────────┤
│ 入力 (left)                            │ プレビュー (right)                 │
│ ─────────────────                      │ ─────────────────                  │
│ 経歴書                                  │ Fit Score (live)                  │
│ [textarea autosize]                    │   ┌──────────────────────────┐    │
│                                        │   │  88 / 100  ↑ +3          │    │
│ 案件票                                  │   └──────────────────────────┘    │
│ [textarea autosize]                    │  Top Skills detected:             │
│                                        │   Python · 5y · AWS               │
│ 入力ヒント:                             │  Match radar (animated):          │
│ - 打ち止めると 800ms 後に再計算         │   Skill 88 / Culture 75 / ...     │
│ - 「Python」追記で +5 pts              │  Pending: idle / 計算中… / done   │
└────────────────────────────────────────┴───────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf09">
  <header><h1>Live Preview</h1></header>
  <div class="wf09__split">
    <section class="wf09__input">
      <h2>経歴書</h2><textarea id="engineer"></textarea>
      <h2>案件票</h2><textarea id="job"></textarea>
      <p class="wf09__hint">打ち止め 800ms 後に再計算</p>
    </section>
    <aside class="wf09__preview" aria-live="polite" aria-busy="false">
      <div class="wf09__score"><strong id="score">--</strong><span id="delta"></span></div>
      <h3>Top Skills</h3><ul id="skills"></ul>
      <h3>Radar</h3><canvas id="radar" width="280" height="280"></canvas>
      <p class="wf09__status" id="status">idle</p>
    </aside>
  </div>
</main>
```

## 4. State Machine

```text
idle ── input (debounce 800ms) ──> computing (preview aria-busy=true, score blur)
computing ── 200             ──> idle (score updates with delta animation)
computing ── error           ──> idle-warn (status="再計算失敗、もう一度入力")
computing ── new input       ──> abort previous, computing (race-condition guard via seq)
```

## 5. Data Flow + API contract

- textarea `input` イベントで `setTimeout` 800ms debounce。
- debounce 完了で `Promise.all([/api/parse engineer, /api/parse job])` → `/api/match`。
- AbortController で前回 fetch を cancel、race condition 防止。
- result の delta = `new_score - prev_score`、`↑` `↓` `→` で表示。

## 6. Design Tokens (override)

```css
.wf09__split { display: grid; grid-template-columns: 1fr 1fr;
                gap: var(--s-3); padding: var(--s-3); height: calc(100vh - 60px); }
.wf09__input textarea { width: 100%; min-height: 200px; background: var(--c-surface);
                         color: var(--c-text); border: 1px solid var(--c-border);
                         border-radius: var(--r-md); padding: var(--s-3); box-sizing: border-box;
                         margin-bottom: var(--s-3); }
.wf09__preview { background: var(--c-surface); border: 1px solid var(--c-border);
                  border-radius: var(--r-lg); padding: var(--s-4);
                  transition: filter 200ms; }
.wf09__preview[aria-busy="true"] { filter: blur(2px); }
.wf09__score strong { font-size: 96px; color: var(--c-accent); }
.wf09__score span { color: var(--c-success); margin-left: var(--s-3); font-size: 24px; }
.wf09__score span[data-dir="down"] { color: var(--c-danger); }
```

## 7. Interaction Spec

- Debounce: 800ms (定数 `DEBOUNCE_MS = 800`)。
- AbortController per cycle、新 input 来たら前回 abort。
- score の数値は count-up animation (300ms、`requestAnimationFrame`)。
- 状態テキスト: `idle` / `計算中…` / `再計算失敗`。
- quota セーフ: `AI_FORCE_MOCK=1` 環境変数を server 側でセットしておくとデモが quota 消費しない (既存仕組み流用)。

## 8. A11y

- `aria-live="polite" aria-busy` で screen reader が更新を読み上げ。
- 数値変化を頻繁に読み上げると煩いので、`aria-live="polite"` + delta 文言だけを announce。
- textarea label は `<h2>` ラベルを `aria-labelledby` で紐付け。
- count-up animation は `prefers-reduced-motion: reduce` で即値に。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 900 | 1 列 (input → preview)、preview sticky-top で常時可視 |
| 901-1280 | 2 列、preview width 40% |
| ≥ 1281 | 2 列、preview width 50%、radar 大きめ |

## 10. Out of Scope

- 履歴 (永続化なし、現在 input の live preview のみ)
- 比較 (→ WF-07)
- WebSocket / SSE (HTTP polling のみ、サーバ実装増加なし)
- 自動保存

## 11. Acceptance Criteria

- [ ] 入力 800ms 静止で /api/parse x2 + /api/match が発火する
- [ ] 連打中は前回 fetch が abort、最後の入力のみ反映 (race condition 0)
- [ ] preview に score / radar / top skills / delta 矢印が表示される
- [ ] 計算中 preview が aria-busy=true + blur で視覚化される
- [ ] `prefers-reduced-motion: reduce` 設定で count-up が即値表示に
- [ ] mobile 1 列で preview が sticky-top でスクロール中も見える
- [ ] verify_public_demo.py pass

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-09 "Inline Live Preview" for Mighty Skill-Bridge as exports/wireframes/wf-09.html.

Stack: vanilla HTML/JS, AbortController. Use POST /api/parse x2 + POST /api/match on debounced
input (800ms).

UX: Two-column split (left input / right preview). Live updates on typing. Score count-up animation,
radar (canvas), top skills list, delta arrow (↑/↓). Preview blurs while computing.
Race-condition guard via AbortController.

Mobile: collapse to 1-col, preview sticky-top. Honor prefers-reduced-motion.

Acceptance: docs/wireframes/WF-09_inline_live_preview.md §11. Quota note: assume AI_FORCE_MOCK=1
during dev to avoid burning Gemini calls. No build, no framework. Single file.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-09 Live Preview</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;
      --c-success:#39FF14;--c-danger:#FF3366;--c-border:#2A2D3E;--r-md:12px;--r-lg:20px;--s-3:16px;--s-4:24px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif}
.wf09__split{display:grid;grid-template-columns:1fr 1fr;gap:var(--s-3);padding:var(--s-3);height:calc(100vh - 80px)}
@media (max-width:900px){.wf09__split{grid-template-columns:1fr}}
textarea{width:100%;min-height:160px;background:var(--c-surface);color:var(--c-text);
         border:1px solid var(--c-border);border-radius:var(--r-md);padding:var(--s-3);box-sizing:border-box;margin-bottom:var(--s-3)}
.wf09__preview{background:var(--c-surface);border:1px solid var(--c-border);
                border-radius:var(--r-lg);padding:var(--s-4);transition:filter .2s}
.wf09__preview[aria-busy="true"]{filter:blur(2px)}
.wf09__score strong{font-size:96px;color:var(--c-accent);display:block;line-height:1}
.wf09__score span{color:var(--c-success);font-size:24px}
.wf09__score span[data-dir="down"]{color:var(--c-danger)}
</style></head><body>
<header style="padding:var(--s-3)"><h1>Live Preview</h1></header>
<main class="wf09__split">
  <section><h2>経歴書</h2><textarea id="eng"></textarea>
    <h2>案件票</h2><textarea id="job"></textarea>
    <p style="color:#888">打ち止め 800ms 後に再計算</p></section>
  <aside class="wf09__preview" id="preview" aria-live="polite" aria-busy="false">
    <p class="wf09__score"><strong id="score">--</strong><span id="delta"></span></p>
    <h3>Top Skills</h3><ul id="skills"></ul>
    <canvas id="radar" width="240" height="240"></canvas>
    <p id="status">idle</p></aside>
</main>
<script>
const DEBOUNCE=800; let timer, ctrl, prev=0;
function debounce(fn){return (...a)=>{clearTimeout(timer); timer=setTimeout(()=>fn(...a),DEBOUNCE)}}
async function compute(){
  const eng=document.getElementById("eng").value.trim();
  const job=document.getElementById("job").value.trim();
  if(!eng||!job) return;
  if(ctrl) ctrl.abort(); ctrl=new AbortController();
  const prev_view=document.getElementById("preview"); prev_view.setAttribute("aria-busy","true");
  document.getElementById("status").textContent="計算中…";
  try{
    const fd1=new FormData();fd1.append("text",eng);fd1.append("doc_type","engineer");
    const fd2=new FormData();fd2.append("text",job);fd2.append("doc_type","job");
    await Promise.all([
      fetch("/api/parse",{method:"POST",body:fd1,signal:ctrl.signal}),
      fetch("/api/parse",{method:"POST",body:fd2,signal:ctrl.signal})]);
    const m=await (await fetch("/api/match",{method:"POST",signal:ctrl.signal,
      headers:{"content-type":"application/json"},
      body:JSON.stringify({engineer_content:eng,job_content:job})})).json();
    const s=m.final_score, d=s-prev;
    document.getElementById("score").textContent=s;
    const dl=document.getElementById("delta");
    dl.textContent= d>0?` ↑ +${d}`: d<0?` ↓ ${d}`: " →";
    dl.dataset.dir = d<0?"down":"up";
    prev=s;
    document.getElementById("skills").innerHTML=(m.scores?
      [`Skill ${m.scores.skill}`,`Culture ${m.scores.culture}`,`Growth ${m.scores.growth}`,`Performing ${m.scores.performing}`]
      .map(x=>`<li>${x}</li>`).join(""):"");
    document.getElementById("status").textContent="idle";
  }catch(e){if(e.name!=="AbortError"){document.getElementById("status").textContent="再計算失敗"}}
  finally{prev_view.setAttribute("aria-busy","false")}
}
const fire=debounce(compute);
document.getElementById("eng").addEventListener("input",fire);
document.getElementById("job").addEventListener("input",fire);
</script></body></html>
```
