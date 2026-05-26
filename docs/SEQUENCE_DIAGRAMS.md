# Mighty Skill-Bridge — シーケンス図集

作成日: 2026-05-26
オーナー: Claude Code レーン (architect / docs)
対象 WBS: T658-extend (関係者向け説明資料)
形式: Mermaid sequence diagram (VSCode + Markdown Preview Mermaid Support / GitHub 標準対応)

---

## 前提

- **本プロジェクト構成**: GitHub Pages (静的公開) + FastAPI (ローカル `python src/app.py`) のハイブリッド
- **認証**: Google Workspace OAuth (`k-umezawa@ml-mightylink.com`) — Sheets / Calendar / Drive / NotebookLM 連携時のみ
- **AI バックエンド**: Gemini 2.x multimodal (live) + 決定的 fallback (同一スキーマ)
- **公開デモのモック動作**: `exports/wireframes/_mock.js` が `fetch()` を monkey-patch し、`/api/*` が 404 のとき固定 hash の mock 応答を返す (バナー赤帯付き)

---

## パターン 1: AI フィット診断フロー (ローカル `python src/app.py`)

> ローカル起動時の本物 Gemini パス。経歴 + 案件 → 4 軸スコア + 推奨質問 + 3 週ロードマップ。

```mermaid
sequenceDiagram
    autonumber
    participant User as User<br/>(ブラウザ)
    participant Root as 公開デモ<br/>(http://localhost:8000/)
    participant API as FastAPI<br/>(src/app.py)
    participant Gemini as Gemini API<br/>(2.x multimodal)
    participant Audit as Audit Log<br/>(exports/audit/)
    participant Fallback as Deterministic<br/>Fallback (BM25 + rules)

    rect rgb(220,235,255)
        Note over User,Root: ① フェーズ1: 公開デモ初期表示
        User->>Root: GET / (公開デモアクセス)
        Root-->>User: index.html (hero / 4-pillar / Step1 入力 UI)
        User->>User: Step1 経歴 + 案件を貼り付け<br/>or Load Sample x2 でサンプル投入
    end

    rect rgb(220,255,220)
        Note over User,Audit: ② フェーズ2: 並列 parse (経歴 + 案件)
        User->>API: POST /api/parse (engineer, text)
        User->>API: POST /api/parse (job, text) — 並列
        par engineer parse
            API->>Gemini: prompt = parse engineer doc<br/>(structured extract)
            Gemini-->>API: parsed_text + structured profile
        and job parse
            API->>Gemini: prompt = parse job doc
            Gemini-->>API: parsed_text + structured profile
        end
        API->>Audit: append_external_api_event<br/>(operation=parse, billable=true)
        API-->>User: 2x { parsed_text, structured, audit }
    end

    rect rgb(255,245,220)
        Note over User,Fallback: ③ フェーズ3: 4 軸 match + ロードマップ生成
        User->>API: POST /api/match { engineer_content, job_content }
        alt Gemini quota 内
            API->>Gemini: prompt = JSON schema 強制<br/>(final_score, scores{4軸}, summary, qa[], roadmap_week1/2/3)
            Gemini-->>API: JSON 応答
        else Gemini quota 枯渇 or live error
            API->>Fallback: build_fallback_match(engineer, job)
            Fallback-->>API: 同一スキーマ (live と差異なし)
            Note over API: 上流クライアントは live/fallback を意識しない
        end
        API->>Audit: append_external_api_event<br/>(operation=match, outcome=success/blocked)
        API-->>User: { final_score, scores, summary, qa, roadmap }
        User->>User: radar chart + gauge + QA accordion 描画
    end
```

---

## パターン 2: 公開 Pages の Mock フォールバック (バックエンドなし環境)

> GitHub Pages から WF / LP / Recruit カタログにアクセスした場合の動作。`_mock.js` が `/api/*` の 404 を検出して固定 hash mock 応答に切り替える。

```mermaid
sequenceDiagram
    autonumber
    participant User as User<br/>(ブラウザ)
    participant Pages as GitHub Pages<br/>(kanta13jp1.github.io/<br/>mighty-link-ai-connect/)
    participant WF as WF Demo<br/>(exports/wireframes/wf-XX.html)
    participant Mock as _mock.js<br/>(fetch monkey-patch)
    participant Banner as デモバナー<br/>(DOM 赤帯)

    rect rgb(220,235,255)
        Note over User,Pages: ① フェーズ1: WF/LP カタログから WF 起動
        User->>Pages: GET /exports/wireframes/wf-03.html
        Pages-->>User: HTML + <script src="_mock.js"></script>
        User->>Mock: スクリプト実行<br/>(window.fetch を上書き)
    end

    rect rgb(255,225,225)
        Note over User,Banner: ② フェーズ2: 実 API の存在確認 → mock 切替
        User->>Mock: GET /api/health (起動時 health check)
        Mock->>Pages: REAL_FETCH("/api/health")
        Pages-->>Mock: HTTP 404 (Pages は静的のみ)
        Mock->>Banner: showBanner()<br/>"🧪 デモモード: バックエンド未接続"
        Banner-->>User: 赤帯バナー表示
    end

    rect rgb(255,245,220)
        Note over User,Mock: ③ フェーズ3: WF 操作 → mock 応答で動作
        User->>WF: 経歴 + 案件を入力 → Analyze
        WF->>Mock: fetch("/api/parse", { engineer })
        Mock->>Pages: REAL_FETCH (404)
        Mock->>Mock: fakeRoute("/api/parse")<br/>= mockParse(text, doc_type)
        Mock-->>WF: { parsed_text: "[MOCK]...", audit: fallback }
        WF->>Mock: fetch("/api/match", { engineer, job })
        Mock->>Mock: fakeRoute("/api/match")<br/>= mockMatch(seed=hash(eng+job))
        Mock-->>WF: { final_score, scores{4軸}, summary, qa, roadmap }
        WF-->>User: スコア・サマリ・ロードマップ描画<br/>(固定 hash で再現性ある mock データ)
    end

    Note over User,Banner: 注: ローカル `python src/app.py` 起動時は<br/>/api/health が 200 → mock は no-op pass-through<br/>= 本物の Gemini が動く
```

---

## パターン 3: 開発フロー (3-tool AI 体制 + WBS / Sheets / Calendar 同期)

> Claude Code (architect/docs/UI) / VSCode + Codex (実装/sync scripts) / Antigravity + Gemini (frontend polish/demo video) の 3-tool 並走。WBS / 課題管理表 / QA表 の 3 タブを Google Sheets に同期、Calendar に WBS イベントを反映 (完了は自動削除)。

```mermaid
sequenceDiagram
    autonumber
    participant Dev as 開発者<br/>(寛太)
    participant Claude as Claude Code<br/>(architect/docs)
    participant Codex as VSCode + Codex<br/>(実装/PR)
    participant Antig as Antigravity + Gemini<br/>(polish/demo)
    participant Repo as GitHub Repo<br/>(mighty-link-ai-connect)
    participant Sheets as Google Sheets<br/>(WBS + Issues + QA)
    participant Cal as Google Calendar<br/>(Mighty Skill-Bridge)
    participant Pages as GitHub Pages<br/>(公開デモ URL)

    rect rgb(220,235,255)
        Note over Dev,Antig: ① フェーズ1: タスク振り分け (3-tool ルール)
        Dev->>Claude: docs / triage / UI design task<br/>(例: HANDOFF-36 採用 LP)
        Claude-->>Dev: PR 作成 → squash merge<br/>([claude] commit prefix)
        Dev->>Codex: 実装 / sync スクリプト編集<br/>(例: data/WBS.tsv の flip)
        Codex-->>Dev: scoped PR → merge ([codex])
        Dev->>Antig: frontend polish / demo video<br/>(Gemini quota 内)
        Antig-->>Dev: 視覚 polish PR ([antigravity])
    end

    rect rgb(220,255,220)
        Note over Dev,Pages: ② フェーズ2: main → master → Pages 反映
        Dev->>Repo: git push origin feat/XXX
        Repo->>Repo: PR squash-merge to main
        Dev->>Repo: git push origin main:master
        Repo->>Pages: GitHub Pages 自動ビルド (master)
        Pages-->>Dev: 公開 URL 反映 (1-2 分)
        Dev->>Repo: python scripts/verify_public_demo.py --url <pages>
        Repo-->>Dev: REQUIRED_MARKERS 確認 + 200 OK
    end

    rect rgb(255,245,220)
        Note over Dev,Cal: ③ フェーズ3: Sheets + Calendar 同期 (毎セッション末)
        Dev->>Sheets: python scripts/sync_wbs_to_sheets.py
        Note over Sheets: WBS / 課題管理表 / QA表 の 3 タブ更新<br/>(同一 OAuth で 3 タブ同時)
        Sheets-->>Dev: 完了 (109 WBS + 55 issues + 48 QA など)
        Dev->>Cal: python scripts/sync_wbs_to_calendar.py
        Note over Cal: WBS の ステータス==完了 行 →<br/>該当 Calendar event を DELETE<br/>(タイトル一致で照合)
        Cal-->>Dev: Active: 13, Updated: 13,<br/>Deleted completed: N
        Dev->>Repo: data/issues_tracker.tsv に<br/>HANDOFF-XX 追記 (resolved)
    end
```

---

## パターン 4: 採用 LP エントリーフロー (HANDOFF-36 で新設)

> 掲載型採用前提の 1 枚 LP。エントリー前に弊社特徴を伝え、`careers@ml-mightylink.com` mailto で接点を作る。Workspace ドメインの社内アドレスで受信。

```mermaid
sequenceDiagram
    autonumber
    participant Cand as 候補者<br/>(社外エンジニア)
    participant SNS as 求人媒体<br/>(Wantedly / X / 紹介)
    participant LP as 採用 LP<br/>(exports/recruit/index.html)
    participant Demo as 公開デモ<br/>(root index.html)
    participant Mail as 候補者のメーラー
    participant Inbox as careers@<br/>ml-mightylink.com<br/>(Workspace)
    participant HR as 採用担当<br/>(寛太 + サポート)

    rect rgb(220,235,255)
        Note over Cand,LP: ① フェーズ1: LP 到達 + 自己理解
        Cand->>SNS: 求人情報を見る
        SNS-->>Cand: LP URL リンクをクリック
        Cand->>LP: GET /exports/recruit/index.html
        LP-->>Cand: Hero (採用 eyebrow + メイン CTA)
        Cand->>LP: scroll → Why us 4-pillar
        LP->>LP: IntersectionObserver で fade-in
        Cand->>LP: scroll → Product highlight
        LP-->>Cand: Skill-Bridge への動線 + サンプル score panel
    end

    rect rgb(220,255,220)
        Note over Cand,Demo: ② フェーズ2: プロダクト体験 (任意)
        Cand->>LP: "プロダクトを見る" CTA クリック
        LP-->>Cand: ../../ (= root index.html) へ遷移
        Cand->>Demo: 公開デモで AI フィット診断を体験
        Note over Demo: パターン2 (Mock フォールバック)<br/>= バナー赤帯 + 固定 hash mock が動作
        Demo-->>Cand: 4 軸スコア + サマリ + roadmap 確認
        Cand->>LP: ブラウザ Back で LP へ戻る
        Cand->>LP: Roles → Process → FAQ を確認
    end

    rect rgb(255,245,220)
        Note over Cand,HR: ③ フェーズ3: エントリー (mailto) → カジュアル面談
        Cand->>LP: "▶ careers@ml-mightylink.com" クリック<br/>(Apply CTA mailto link)
        LP->>Mail: mailto:careers@... 起動<br/>(subject / body プリフィル)
        Mail-->>Cand: 候補者のメーラーに自動作成<br/>(お名前 / 興味ロール / 自己紹介 URL の空欄)
        Cand->>Inbox: 必須欄を埋めて送信
        Inbox->>HR: Workspace 受信 (k-umezawa@ml-mightylink.com 配下)
        HR->>Cand: 24h 以内に返信 (カジュアル面談 30 分の日程調整)
        Note over Cand,HR: その後の 4-step process:<br/>カジュアル面談 → 技術対話 → 1 日 trial → オファー<br/>(最短 2 週間で完了)
    end
```

---

## メモ

- **編集方針**: 各図は **1 画面 1 シナリオ**で完結。フェーズ番号 (①/②/③) でストーリーを区切り、関係者+システムを縦軸、時系列を縦方向に並べる。`rect rgb(...)` でフェーズの色分け。
- **Mermaid 標準対応**: GitHub Markdown プレビュー、VSCode 拡張 (`bierner.markdown-mermaid` 等)、Notion (`/mermaid`)、Obsidian でそのまま描画可能。
- **更新トリガ**: API endpoint 追加 / 認証フロー変更 / 開発フロー再編 が起きたら本書を更新。古いシーケンスは「Stale」セクションへ退避ではなく**物理削除**で運用する ([feedback_stale_doc_deletion](../../../.claude/projects/.../memory/feedback_stale_doc_deletion.md) 方針)。
- **関連 docs**:
  - [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) — 3-tool 体制の handoff 規約
  - [BACKEND_AI_PIPELINE.md](BACKEND_AI_PIPELINE.md) — Gemini live / fallback の設計詳細
  - [SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md) — Sheets 3 タブのスキーマ
  - [SETUP_GUIDE.md](SETUP_GUIDE.md) — 環境構築と sync スクリプト実行
