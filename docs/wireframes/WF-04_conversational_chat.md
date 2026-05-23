# WF-04 · Conversational Chat — AI Interview

> Subtitle: AI が質問 / ユーザーが回答 / 最終 fit を結果バブルで提示。
> 💡 Rationale: 応募者本人が直接使う場合に親しみやすい。チャット履歴で説明責任。

## 1. Identity

| key | value |
| --- | --- |
| id | `WF-04` |
| category | conversational / chat |
| status | spec-ready (visual = Canva slide 5) |
| pick-when | 応募者本人が直接利用、説明責任が必要、AI ライブ感重視 |
| skip-when | HR 一括処理 / multi-candidate 比較 |
| output target | `static/wireframes/wf-04.html` |

## 2. ASCII Layout

```text
┌─────────────────────── 800 width ────────────────────────────┐
│  Mighty AI Interview                              [Reset] [⚙]│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🤖 AI: こんにちは。まず経歴書を貼ってください。              │
│                                                              │
│         👤 You: [経歴貼付]                                    │
│                                                              │
│  🤖 AI: 受け取りました。次に案件票をお願いします。           │
│                                                              │
│         👤 You: [案件貼付]                                    │
│                                                              │
│  🤖 AI: 分析中... ⌛                                          │
│                                                              │
│  🤖 AI: フィット 88 / 100。理由は ...                         │
│        [Card: Score gauge + summary]                         │
│        [Card: QA 推奨質問 1/2]                                │
│        [Card: Roadmap week1/2/3]                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ [textarea autosize] [📎] [➤ Send]                            │
└──────────────────────────────────────────────────────────────┘
```

## 3. Component Tree

```html
<main class="wf04" role="log" aria-label="AI interview transcript">
  <header><h1>Mighty AI Interview</h1><button data-act="reset">Reset</button></header>
  <ol class="wf04__messages" id="messages"></ol>
  <form class="wf04__composer" id="composer">
    <textarea id="input" rows="1" placeholder="メッセージを入力..."></textarea>
    <label class="btn">📎<input type="file" hidden></label>
    <button type="submit">➤ Send</button>
  </form>
</main>
<template id="msg-tpl">
  <li class="wf04__msg"><span class="wf04__avatar"></span><div class="wf04__bubble"></div></li>
</template>
```

## 4. State Machine

```text
init     ── system msg ──> awaiting-engineer
awaiting-engineer ── user msg ──> parsing-engineer
parsing-engineer ── 200 ──> awaiting-job
awaiting-job ── user msg ──> parsing-job
parsing-job ── 200 ──> matching
matching ── 200 ──> done (result cards rendered)
matching ── error ──> awaiting-job (retry hint)
any ── reset ──> init
```

## 5. Data Flow + API contract

- 初回 system message を AI bubble としてプッシュ。
- user message 1 (engineer) → `POST /api/parse` (`doc_type=engineer`) → parsed_text を 内部保持、bubble は user に出した raw text のまま。
- user message 2 (job) → `POST /api/parse` (`doc_type=job`)。
- 両 parse 完了で `POST /api/match` → score / summary / qa / roadmap を **複数 bubble** で順番に push。

## 6. Design Tokens (override)

```css
.wf04 { max-width: 800px; margin: 0 auto; display: grid;
        grid-template-rows: auto 1fr auto; height: 100vh; }
.wf04__messages { list-style:none; padding: var(--s-3); margin:0;
                  overflow-y: auto; display: grid; gap: var(--s-3); }
.wf04__msg { display:grid; grid-template-columns: 40px 1fr; gap: var(--s-3); }
.wf04__msg--user { grid-template-columns: 1fr 40px; }
.wf04__bubble { background: var(--c-surface); padding: var(--s-3);
                border-radius: var(--r-lg); border: 1px solid var(--c-border); }
.wf04__msg--user .wf04__bubble { background: var(--c-accent); color: var(--c-bg); }
.wf04__composer { display:grid; grid-template-columns: 1fr auto auto;
                  gap: var(--s-2); padding: var(--s-3); border-top: 1px solid var(--c-border); }
```

## 7. Interaction Spec

- textarea: Enter で送信、Shift+Enter で改行 (composer-input handler)。
- 送信中は composer disable + spinner avatar 表示。
- new bubble 追加時に `messages.scrollTop = messages.scrollHeight` で auto-scroll。
- typing indicator: AI 応答待ち中、AI bubble に三点アニメ ("…")。

## 8. A11y

- `role="log" aria-live="polite"` で screen reader が新 message を読む。
- 各 bubble: user は `<li aria-label="あなた: ...">`、AI は `<li aria-label="AI: ...">`。
- composer textarea は label = "メッセージを入力"。
- Reset は `<button type="button">`、confirm dialog 推奨。

## 9. Responsive

| breakpoint | layout |
| --- | --- |
| ≤ 600 | full viewport、composer sticky-bottom、bubble max 80% |
| 601-1024 | max-width 720、center、composer sticky-bottom |
| ≥ 1025 | max-width 800、composer 通常 flow |

## 10. Out of Scope

- 過去 transcript 永続化 (sessionStorage のみ、DB なし)
- マルチターン本格対話 (single-shot match のみ、follow-up question は QA cards で代替)
- 音声入力 / TTS

## 11. Acceptance Criteria

- [ ] AI が最初に経歴を求める system message を出す
- [ ] user が経歴貼付 → AI が parse 完了確認 → 案件要求 → 結果まで一往復で到達
- [ ] result が 3 種 bubble (score / qa / roadmap) で順番に出る
- [ ] Reset で全 message が消え、初期 system message のみ残る
- [ ] mobile で composer が virtual keyboard 出現時に隠れない (`@supports (height: 100dvh)`)
- [ ] keyboard only で送信完走 (Enter で送れる)

## 12. Implementation Prompt (LLM-ready)

```text
Implement WF-04 "Conversational Chat" for Mighty Skill-Bridge as static/wireframes/wf-04.html.

Stack: vanilla HTML/JS. Use POST /api/parse twice (engineer then job), then POST /api/match.

UX: AI initiates with system message asking for engineer profile. User pastes text → AI confirms via
bubble → asks for job. After both parsed → AI shows "matching..." → emits 3 result bubbles
(score gauge, QA cards, roadmap).

Tokens: docs/wireframes/README.md. Acceptance: docs/wireframes/WF-04_conversational_chat.md §11.

Do not touch root index.html. Single file output.
```

## 13. Starter Snippet

```html
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WF-04 Conversational Chat</title>
<style>
:root{--c-bg:#0D0E15;--c-surface:#161824;--c-text:#F1F5FF;--c-accent:#00F0FF;
      --c-border:#2A2D3E;--r-lg:20px;--s-2:8px;--s-3:16px}
body{margin:0;background:var(--c-bg);color:var(--c-text);font-family:"Yu Gothic UI",sans-serif;
     height:100dvh;display:grid}
.wf04{max-width:800px;margin:0 auto;width:100%;display:grid;
      grid-template-rows:auto 1fr auto;height:100dvh}
header{padding:var(--s-3);border-bottom:1px solid var(--c-border)}
.wf04__messages{list-style:none;padding:var(--s-3);margin:0;overflow-y:auto;display:grid;gap:var(--s-3)}
.wf04__msg{display:flex;gap:var(--s-2);max-width:80%}
.wf04__msg--user{margin-left:auto;flex-direction:row-reverse}
.wf04__bubble{background:var(--c-surface);padding:var(--s-3);border-radius:var(--r-lg);
              border:1px solid var(--c-border);white-space:pre-wrap}
.wf04__msg--user .wf04__bubble{background:var(--c-accent);color:var(--c-bg)}
.wf04__composer{display:grid;grid-template-columns:1fr auto;gap:var(--s-2);
                padding:var(--s-3);border-top:1px solid var(--c-border)}
textarea{background:#0a0b12;color:var(--c-text);border:1px solid var(--c-border);
         border-radius:12px;padding:var(--s-3);resize:none;font:inherit}
button{background:var(--c-accent);color:var(--c-bg);border:0;border-radius:12px;padding:0 var(--s-3);font-weight:700}
</style></head><body>
<main class="wf04">
  <header><strong>Mighty AI Interview</strong></header>
  <ol class="wf04__messages" id="msgs" role="log" aria-live="polite"></ol>
  <form class="wf04__composer" id="cmp">
    <textarea id="inp" rows="1" placeholder="..."></textarea>
    <button type="submit">➤</button>
  </form>
</main>
<script>
const state={step:"engineer", engineer:"", job:""};
const $=s=>document.querySelector(s);
function push(role, text){
  const li=document.createElement("li");
  li.className="wf04__msg "+(role==="user"?"wf04__msg--user":"");
  const b=document.createElement("div"); b.className="wf04__bubble"; b.textContent=text;
  li.appendChild(b); $("#msgs").appendChild(li); $("#msgs").scrollTop=1e9;
}
push("ai","こんにちは。まず経歴書を貼り付けてください。");
$("#cmp").addEventListener("submit", async e=>{
  e.preventDefault(); const t=$("#inp").value.trim(); if(!t) return;
  push("user", t); $("#inp").value="";
  if(state.step==="engineer"){state.engineer=t;
    const fd=new FormData();fd.append("text",t);fd.append("doc_type","engineer");
    await fetch("/api/parse",{method:"POST",body:fd});
    push("ai","受け取りました。次に案件票をお願いします。"); state.step="job"; return;}
  if(state.step==="job"){state.job=t;
    const fd=new FormData();fd.append("text",t);fd.append("doc_type","job");
    await fetch("/api/parse",{method:"POST",body:fd});
    push("ai","分析中..."); state.step="done";
    const m=await (await fetch("/api/match",{method:"POST",
      headers:{"content-type":"application/json"},
      body:JSON.stringify({engineer_content:state.engineer,job_content:state.job})})).json();
    push("ai", `フィット ${m.final_score}/100\n${m.summary}`);
    push("ai", "推奨質問:\n"+(m.qa||[]).map(q=>"・"+q.question).join("\n"));
    push("ai", `週 1: ${m.roadmap_week1}\n週 2: ${m.roadmap_week2}\n週 3: ${m.roadmap_week3}`);
  }
});
$("#inp").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();$("#cmp").requestSubmit();}});
</script></body></html>
```
