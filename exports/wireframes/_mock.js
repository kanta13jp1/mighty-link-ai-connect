// Mighty Skill-Bridge — WF demo mock shim
// Intercepts /api/* fetches and returns canned responses when the real
// FastAPI backend is unreachable (e.g. when served from GitHub Pages).
// When run locally (python src/app.py) the real backend responds 200 and
// this shim is a no-op pass-through.
(function () {
  const REAL_FETCH = window.fetch.bind(window);

  const SCORE = (seed) => 60 + Math.abs(hash(seed) % 41);  // 60..100
  function hash(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) { h = (h * 31 + s.charCodeAt(i)) | 0; }
    return h;
  }
  function mkResp(obj, status = 200) {
    return new Response(JSON.stringify(obj), {
      status,
      headers: { "content-type": "application/json" },
    });
  }
  async function readBody(init) {
    if (!init) return "";
    if (init.body instanceof FormData) {
      const o = {};
      for (const [k, v] of init.body.entries()) o[k] = v;
      return JSON.stringify(o);
    }
    if (typeof init.body === "string") return init.body;
    return "";
  }
  function mockParse(text, doc_type) {
    const summary = (text || "").slice(0, 120).replace(/\s+/g, " ");
    return {
      parsed_text: `[MOCK ${doc_type}] ${summary || "(empty)"}`,
      structured: { doc_type, summary, length: (text || "").length },
      audit: { ai_mode: "fallback", fallback_reason: "GitHub Pages — no backend" },
    };
  }
  function mockMatch(engineer_content, job_content) {
    const seed = (engineer_content || "") + "|" + (job_content || "");
    const final = SCORE(seed);
    return {
      final_score: final,
      scores: {
        skill: SCORE(seed + "skill"),
        culture: SCORE(seed + "culture"),
        growth: SCORE(seed + "growth"),
        performing: SCORE(seed + "performing"),
      },
      summary: "（モックデータ）GitHub Pages 上ではバックエンド API が利用できないため、固定 hash ベースのサンプルスコアを返しています。実機 (ローカル `python src/app.py`) で本物の Gemini 評価が動きます。",
      qa: [
        { question: "本案件で最も貢献できる技術領域は?", answer: "（モック）経歴の上位スキルを案件必須技術に対応付け、過去 PJ の規模感を添える。", tip: "数字 (req/s, ユーザー数) を 1 つ入れる" },
        { question: "ギャップ領域はどう埋める?", answer: "（モック）週 1 OSS + 週 2 社内 PoC で 4 週間以内にカバー。", tip: "学習計画を 1 週単位で示す" },
      ],
      roadmap_week1: "（モック）環境構築 + コードベース walkthrough + on-call shadow",
      roadmap_week2: "（モック）小規模 PR 3 本 + on-call primary 半週",
      roadmap_week3: "（モック）SLI/SLO レビュー参加 + skill gap topic を内部勉強会で共有",
      audit: { ai_mode: "fallback", fallback_reason: "GitHub Pages — no backend" },
    };
  }
  function mockAudit() {
    const events = [];
    for (let i = 0; i < 12; i++) {
      events.push({
        type: "match",
        operation: "match",
        final_score: SCORE("mock" + i),
        timestamp: new Date(Date.now() - i * 3600_000).toISOString(),
        payload: { final_score: SCORE("mock" + i) },
      });
    }
    return { events };
  }
  function mockUsage() {
    return { calls: 142, total_calls: 142, fallback_rate: 0.12, p95_latency_ms: 1200 };
  }

  async function fakeRoute(url, init) {
    const u = new URL(url, location.origin);
    const path = u.pathname;
    if (path === "/api/parse") {
      const body = await readBody(init);
      let data = {};
      try { data = JSON.parse(body); } catch (_) {}
      return mkResp(mockParse(data.text || "", data.doc_type || "engineer"));
    }
    if (path === "/api/match") {
      const body = await readBody(init);
      let data = {};
      try { data = JSON.parse(body); } catch (_) {}
      return mkResp(mockMatch(data.engineer_content || "", data.job_content || ""));
    }
    if (path === "/api/audit/recent") return mkResp(mockAudit());
    if (path === "/api/admin/usage") return mkResp(mockUsage());
    return new Response("not found", { status: 404 });
  }

  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const isApi = url.startsWith("/api/") || url.includes(location.origin + "/api/");
    if (!isApi) return REAL_FETCH(input, init);
    try {
      const r = await REAL_FETCH(input, init);
      if (r.ok) return r;
      console.warn("[wf-mock] real fetch returned", r.status, "→ falling back");
      return fakeRoute(url, init);
    } catch (err) {
      console.warn("[wf-mock] real fetch failed:", err.message, "→ falling back");
      return fakeRoute(url, init);
    }
  };

  // Tiny banner so users know they're on mock data
  window.addEventListener("DOMContentLoaded", () => {
    REAL_FETCH("/api/health").then((r) => {
      if (r.ok) return; // real backend available, no banner
      showBanner();
    }).catch(() => showBanner());
  });
  function showBanner() {
    if (document.getElementById("wf-mock-banner")) return;
    const b = document.createElement("div");
    b.id = "wf-mock-banner";
    b.style.cssText =
      "position:fixed;top:0;left:0;right:0;z-index:9999;background:#FF3366;color:#0D0E15;" +
      "font:600 13px/1 'Yu Gothic UI',sans-serif;padding:6px 16px;text-align:center;" +
      "box-shadow:0 2px 8px rgba(0,0,0,0.4)";
    b.textContent =
      "🧪 デモモード: バックエンド API は未接続、固定 hash のモック応答を表示中。実 API は `python src/app.py` ローカル起動で利用可。";
    document.body.appendChild(b);
    document.body.style.paddingTop = "32px";
  }
})();
