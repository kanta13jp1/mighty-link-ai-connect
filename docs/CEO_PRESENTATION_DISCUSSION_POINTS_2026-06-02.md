# 6/2 社長打ち合わせ 論点・選択肢・確認質問リスト (T605)

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン (本ファイルの維持) / 当日進行は人間 + Codex 共同
対応 WBS: **T605** 選択肢整理 (5/26-5/28 予定 → 5/22 前倒し完遂)
関連: [CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) / [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) / [CEO_PRESENTATION_QA_PACK_2026-06-02.md](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607) / [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md)

---

## このドキュメントの位置づけ

[CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) が「比較表 (判断マトリクス)」、本書は「**論点 → 選択肢 → 当日 CEO に聞く確認質問**」の対応関係を構造化したもの。社長打ち合わせ進行役 (Codex/人間) が本書の `D-x` 番号順に進めれば、決定漏れなく当日を回せる設計。

決定 (Decide today) / 保留可 (Defer ok) / 不要 (Out of scope) を各論点で明示し、6/2 終了時に「決まったか」「先送りしたか」「言及しなかったか」を整理できる。

---

## 構造化

| 区分 | 件数 | 用途 |
| --- | --- | --- |
| D 系 (Must decide today) | 6 件 | 6/2 中に必ず社長から回答を得る論点 |
| C 系 (Confirm today) | 4 件 | 既存方針 / 既存実装の確認 (5 分以内に確認) |
| O 系 (Optional / 6/2 中に時間が余れば) | 4 件 | 余裕があれば取り扱う論点 |
| X 系 (Out of scope 6/2) | 3 件 | 当日触れない論点。意図的に防衛するため明示 |

合計 17 論点。

---

## D-1: サービス方向性

**論点**: 本プロトタイプ (Mighty Skill-Bridge) を何のサービスとして育てるか。

**選択肢** (詳細比較は [DECISION_PACK 判断マトリクス](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#判断マトリクス) 参照):
- A. AI フィット診断支援 — 経歴書 × 案件票の 4 軸マッチング
- B. Workspace 連携型 PM 支援 — WBS / Sheets / Calendar / Drive の統合管理
- C. AI PoC 高速構築支援 — 新規事業向けデモ高速ジェネレータ
- D. **保留** — 6/2 で決めず、5-7 営業日以内に追加面談で決める

**社長への確認質問**:
- Q1. A / B / C / D のいずれを最初の柱とするか
- Q2. (A 選択なら) 最初の対象業務は **採用 / 営業 / SES 案件配属** のどれか
- Q3. (B 選択なら) 最初の管理対象は **マイティリンク社内 / 既存顧客 / その両方** のどれか
- Q4. (C 選択なら) PoC 化したい顧客 / 案件はすでにあるか

**当日決まらなかった場合の handoff**: D 選択 → docs/POST_CEO_FOLLOWUP_2026-06-XX.md を Codex レーンが翌日に起票。

---

## D-2: 対象ユーザー (フェルソナ)

**論点**: 最初に価値を届ける具体ユーザー像。

**選択肢**:
- A. **社内利用者** (営業/人材担当/PM) — 最も低リスク、社内データで検証可能
- B. **既存顧客** (マイティリンクの既存取引先) — 関係性ベースの実証実験が可能
- C. **見込み顧客** (新規) — 早期の市場検証が可能だが営業リソース必要
- D. A + B 併用

**社長への確認質問**:
- Q1. 最初の検証パイロットを社内 / 既存顧客 / 見込み顧客のどれで打つか
- Q2. (B 選択なら) 候補顧客は何社、いつまでに声をかけるか
- Q3. (C 選択なら) 営業チャネルはどう確保するか

---

## D-3: 最優先機能 (6/2 〜 6/16 の 2 週間で作るもの)

**論点**: 6/2 以降の最初の 2 週間で実装/磨くべき機能。

**選択肢** (現状実装に対する増分で記述):
- A. AI スコア根拠の説明強化 — `score_skill/culture/growth/performing` の根拠 UI を厚くする
- B. 案件候補ストック管理 — 複数案件と複数エンジニアの突合ビュー
- C. 面接質問生成の品質向上 — Gemini live + structured context で interview_questions を磨く
- D. WBS-UI 統合 — WBS 進捗を本 UI 内で操作できるようにする
- E. AI 監査ログ可視化 — `/api/audit/recent` を UI で見せる
- F. デモ用 PoC テンプレート機能 — 顧客名で資料を瞬時生成

**社長への確認質問**:
- Q1. A-F のうち最重要 1 つ + 次点 1 つを選んでほしい
- Q2. 残りは保留 / 不要 / いつかやる、どれに分類するか

---

## D-4: AI エンジン選定方針 (2026-05-22 新規論点)

**論点**: Gemini ファミリーに張るか、複数 AI を比較しながら進めるか。Best Practices Refresh ([MULTI_AI_WORKFLOW.md Best Practices Refresh](MULTI_AI_WORKFLOW.md#best-practices-refresh-2026-05-22)) では **固定の未来モデル名や未確認の公開時期を判断材料にしない** ことを確認済み。毎セッション開始時にGemini API公式モデル一覧を確認し、現行モデルの品質・速度・コスト・quotaで選ぶ。

**選択肢**:
- A. **Gemini ファミリー単一 commit** — 公式モデル一覧で確認した現行Flash/Pro/マルチモーダル対応モデルを中心にする
- B. **マルチ AI 並走** — Gemini + Claude + GPT-5.5 を機能別に使い分け
- C. **Gemini + Claude 二択** — Claude を docs/review/triage に、Gemini を実装/UI/マルチモーダルに
- D. **未定** — 6/2 では決めない

**社長への確認質問**:
- Q1. A / B / C / D のどれを採用するか
- Q2. (B 選択なら) 各 AI のコスト上限を月いくらに置くか

**補足**: 開発体制としては既に C に近い 3-tool 構成 (Antigravity+Gemini / Codex / Claude Code) が走っている ([MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md))。「サービスの中で使う AI エンジン」と「開発に使う AI ツール」は別問題なので混同しないこと。

---

## D-5: 公開範囲

**論点**: 現公開 URL (`https://kanta13jp1.github.io/mighty-link-ai-connect/`) と今後の公開範囲。

**選択肢**:
- A. **社長共有のみ維持** (現状) — 限定共有 URL のまま
- B. **社内共有** — マイティリンク全社員へ展開
- C. **既存顧客への共有** — 既存取引先に見せ始める
- D. **外部公開** — ロゴ・ブランドガード後にウェブ公開

**社長への確認質問**:
- Q1. 6/2 時点で B / C / D のいずれに進めるか、それとも A 維持か
- Q2. 個人情報 / 機密情報を含む経歴書を入力する利用シーンを想定するなら、認証/SSO はいつまでに必要か

---

## D-6: 連携ツール採用判断 (NotebookLM / Slack / Notion / Obsidian)

**論点**: 開発フローへの正式採用優先順位。

**選択肢** (各ツールごとに 採用 / 保留 / 後回し / 不要):
- NotebookLM — 既に CLI + Workspace OAuth 連携済、21 docs source ready
- Slack — CLI / MCP 未露出 ([R3](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点))、投稿草稿のみ
- Notion — MCP 経由で証跡ページ作成済
- Obsidian — vault 雛形 + `.obsidian` config 済、ローカル運用前提

**社長への確認質問**:
- Q1. 6/2 以降に **正式採用** するツールはどれか (採用 = 通知 / 議事録 / 知識管理を本運用)
- Q2. **保留** (お試し継続) はどれか
- Q3. **後回し** (3 ヶ月以上先) はどれか
- Q4. **不要** はどれか

**当日決まらなかった場合**: 現状の「お試し継続」を全ツールに適用、6/16 までに本決定。

---

## C-1: 公開デモ URL の安定性確認

**論点**: 公開 URL が README fallback ではなく本デモ UI を返すこと。

**確認** (5 分以内、社長と画面共有しながら):
- `https://kanta13jp1.github.io/mighty-link-ai-connect/` を開いて Skill-Bridge UI が出ることを目視
- `python scripts/verify_public_demo.py` の green を見せる

**確認質問**: 「これで OK ですか」だけ。問題なければ通過。

## C-2: Google Workspace OAuth 状態確認

**論点**: `k-umezawa@ml-mightylink.com` で Drive / Calendar / Sheets が活きていること。

**確認**: `python scripts/verify_google_workspace_account.py` の出力を見せる。

## C-3: Gemini quota 状態

**論点**: 5/27 18:48 の refresh 待ち状態であること、demo は deterministic fallback で支障なし。

**確認**: `/api/health` の `ai_mode: deterministic_fallback` を見せる。

## C-4: 連携実装証跡

**論点**: NotebookLM / Notion / Drive / GitHub Issues の証跡が docs にまとめられていること。

**確認**: [INTEGRATION_DEMO_EVIDENCE_2026-06-02.md](INTEGRATION_DEMO_EVIDENCE_2026-06-02.md) を 30 秒スクロール。

---

## O-1: WBS UI 内製化

**論点**: 現在 Google Sheets WBS を見せているが、本 UI 内に統合する価値があるか。

**選択肢**: 統合する / 当面 Sheets のまま / Notion 移管。

**社長への確認質問**: 「Sheets 維持 / 内製化 / Notion 移管」3 択。

## O-2: 課金モデル仮説

**論点**: 6/2 までは決め打ちしない方針 (PREP.md:77)。ただし方向性 A/B/C で課金モデルが大きく異なるので 5 分だけ触れる価値あり。

**選択肢**: 月額 SaaS / 案件あたり従量 / 顧問契約 / 一括導入。

## O-3: ロゴ / ブランディング

**論点**: 現状は仮ロゴ。外部公開 (D-5 で D 選択) 時に必要。

**確認質問**: 「公開時にロゴ刷新するか」のみ。

## O-4: チーム拡大シナリオ

**論点**: 6/2 以降に 1 名追加採用するならどの役割か。

**選択肢**: フロントエンジニア / バックエンジニア / PM / 営業。

---

## X-1: 正式サービス名

**論点**: PREP.md:76 で「6/2 まで決め打ちしない」と既に確定済。当日に名称検討は持ち込まない。

## X-2: 本番運用範囲 / SLA

**論点**: PREP.md:78 で「6/2 まで決め打ちしない」と既に確定済。SLA や本番稼働コミットは出さない。

## X-3: 営業資料 / 告知文 / プレスリリースの確定版

**論点**: PREP.md:81 で「6/2 まで決め打ちしない」と既に確定済。告知タイミングは方向性確定後 1 週間以内に Claude/Gemini で起草。

---

## 6/2 当日進行 (90 分想定)

| Phase | 時間 | 論点 | 進行 |
| --- | --- | --- | --- |
| Opening | 5 分 | 本日のゴール提示 | 司会 (人間) |
| Status check | 10 分 | C-1 〜 C-4 を一気に流す | デモ操作 (Codex / 人間) |
| Direction | 30 分 | **D-1 / D-2** | 議論メイン |
| Scope | 20 分 | **D-3 / D-4** | 議論メイン |
| Exposure | 10 分 | **D-5 / D-6** | 確認ベース |
| Optional | 10 分 (余れば) | O-1 〜 O-4 から | 時間に応じて |
| Wrap | 5 分 | 議事録テンプレート埋め | 議事録係 (Claude Code レーンが事前準備) |

---

## 関連 docs と最新化フロー

- [CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) #6/2で決める事項 と本書 D 系は対応関係。**矛盾があれば本書を優先**して PREP.md を Claude Code レーンが更新。
- [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) #判断マトリクス は本書 D-1 の補足。
- [CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) E 系 (判断材料) に本書を `E-1' 論点リスト構造化` として追加する候補。

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (T605 完遂、D 系 6 / C 系 4 / O 系 4 / X 系 3 = 17 論点) |
