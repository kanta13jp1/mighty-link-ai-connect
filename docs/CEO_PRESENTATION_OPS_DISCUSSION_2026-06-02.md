# 6/2 社長打ち合わせ 運用・体制・リスク・費用感 論点 (T606)

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン
対応 WBS: **T606** 運用・体制論点 (5/28-5/29 予定 → 5/22 前倒し完遂)
関連: [DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (T605) / [QA_PACK](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607) / [DECISION_PACK](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) (T611) / [MULTI_AI_WORKFLOW](MULTI_AI_WORKFLOW.md)

---

## このドキュメントの位置づけ

[T605 DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) は「6/2 で何を決めるか」、[T607 QA_PACK](CEO_PRESENTATION_QA_PACK_2026-06-02.md) は「予想される質問への回答」。本書はその間を埋める **「6/2 以降の運用・体制・リスク・費用」を社長と握るための論点パック** (T606 deliverable)。

サービス方向性 (D-1) が決まった後、現実に **「誰が・どのリソースで・どの費用感で運用するか」** を確認しなければ着手できない。本書は方向性別の運用シナリオを 1 箇所に集約し、当日 30 分の Operations フェーズで使う。

---

## 1. 開発体制 (現状 + 6/2 後)

### 1.1 現状 (2026-05-22 時点)

| 役割 | 担当 | 工数 / 週 | 備考 |
| --- | --- | --- | --- |
| Orchestrator (寛太) | 人間 1 名 | 15-20h | 3-tool 並走の見張り、PR レビュー、社長コミュニケーション |
| Antigravity + Gemini レーン | AI | (主作業環境、quota 制約あり) | UI / マルチモーダル / 長文推論 |
| VSCode + Codex レーン | AI | (24h 稼働可、Gemini quota 独立) | 実装 PR / SQL / CI / sync スクリプト / gh CLI |
| VSCode + Claude Code レーン | AI | (Gemini quota 独立) | docs / triage / WBS 調停 / 本書執筆 |

詳細は [MULTI_AI_WORKFLOW.md 3-Tool 構成](MULTI_AI_WORKFLOW.md#3-tool-構成)。

### 1.2 6/2 後シナリオ (サービス方向性別)

| シナリオ | 寛太の役割 | 追加採用 | 6/16 までの工数 |
| --- | --- | --- | --- |
| **A (AI フィット診断)** | プロダクト + 営業窓口 | 6/16 時点では不要、社内パイロット結果次第で 7-8 月に営業 1 名 | 15h/週 維持 |
| **B (Workspace 連携型 PM)** | プロダクト + 既存顧客フォロー | 不要 (Workspace ベースで既存顧客が自走しやすい) | 10h/週 で安定可能 |
| **C (PoC 高速構築)** | プロダクト + 案件営業 | 顧客 3 社以上同時で開発 1 名追加検討 | 20-25h/週 (案件次第) |

### 1.3 社長への確認事項

- Q-OPS-01: 6/16 以降の **寛太の関与度**は維持 / 拡大 / 縮小のどれを想定するか
- Q-OPS-02: 追加採用判断は **顧客 3 社同時パイロット時** を閾値にしてよいか
- Q-OPS-03: 3 AI ツール並走の **コスト上限** は月いくらに置くか (現状ほぼ無料、本格化で月 1-5 万円想定)

---

## 2. 運用責任分担 (6/2 後)

### 2.1 5 正本 ([FLEET-OPS 規約](MULTI_AI_WORKFLOW.md))

| 正本 | 場所 | 更新責任 | 閲覧 |
| --- | --- | --- | --- |
| WBS 進捗 | Google Sheets `Mighty-Link WBS` | Codex (data/WBS.tsv 経由) | 社長 / 寛太 |
| Issues / PR | GitHub | Codex (実装) / Claude (review) | 寛太 |
| 課題管理 | Google Sheets `課題管理表` (NEW) | Claude (data/issues_tracker.tsv 経由) | 社長 / 寛太 |
| 想定 QA | Google Sheets `QA 表` (NEW) | Claude (data/qa_tracker.tsv 経由) | 寛太 (社長は当日のみ) |
| 連携証跡 | docs/INTEGRATION_DEMO_EVIDENCE_*.md + Notion | Codex (作成) / Claude (整合性) | 社長 (要求時) |

### 2.2 社長の関与パターン

| パターン | 頻度 | 何を見るか |
| --- | --- | --- |
| **定例レビュー** (推奨) | 隔週 30 分 | Sheets WBS Summary + 課題管理表 HIGH 件のみ |
| **イベント発生時** | 都度 | PR (`risk:ceo-blocker` ラベル) + Slack 通知 (採用時) |
| **打ち合わせ** | 月 1 回 60 分 | DISCUSSION_POINTS 形式の論点パック |

### 2.3 社長への確認事項

- Q-OPS-04: 定例レビュー (隔週 30 分) を 6/16 以降に固定スケジュール化してよいか
- Q-OPS-05: `risk:ceo-blocker` ラベル PR の通知先 (メール / Slack / Notion) はどれを正にするか
- Q-OPS-06: 6/2 で決めた方向性ごとに、社長レビュー粒度を変えるか (例: A = 月次、B = 隔週、C = 案件ごと)

---

## 3. リスク管理 (現状の R1-R8 + 6/2 後の新規)

### 3.1 現状リスク

詳細は [CEO_PRESENTATION_PREP_2026-06-02.md Risks & Blockers](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点) (R1-R8)。本書では 6/2 で社長判断が必要なものに絞る:

- **R2** (HIGH) GitHub Project `read:project` scope 不足 → 6/2 までに復旧不可なら **Project ボード除外**を社長承認
- **R3** (MED) Slack live send 不可 → 草稿表示で代替、live 送信は 6/2 後の D-6 連携採用判断に依存
- **R8** (LOW) サービス方向性が 6/2 で決まらない場合 → 5-7 営業日以内の追加面談を予約

### 3.2 6/2 後に発生する想定リスク (新規)

| ID | 重要度 | リスク | 影響 | 対応案 | 社長判断必要 |
| --- | --- | --- | --- | --- | --- |
| R9 | HIGH | パイロット顧客の経歴書/個人情報の取り扱い (方向性 A 選択時) | 法務 / コンプラ違反 | 利用同意書テンプレート作成、Workspace 内クローズで運用 | YES (法務確認時期) |
| R10 | MED | 公開 URL の外部漏洩 (方向性 A/C 選択時) | デモ環境への意図しないアクセス | basic auth or IP 制限導入 | YES (採用可否) |
| R11 | MED | 3 AI ツール並走の月額コスト超過 | 予算超過 | quota メーター監視 + 月次レポート、超過時の優先 lane 決定 | YES (上限値) |
| R12 | LOW | Antigravity 2.0 の Managed Agents tier コスト | Enterprise tier への switch コスト発生 | I/O 2026 で発表された Managed Agents API の料金監視 | NO (Codex/Claude が監視) |
| R13 | LOW | 寛太のリソース集中による単一障害点 | 寛太が稼働不可になるとプロジェクト停止 | docs/CODEX_CONTINUATION_NOTES.md と docs/MULTI_AI_WORKFLOW.md で再現性確保中 | NO |

### 3.3 社長への確認事項

- Q-OPS-07: R9 個人情報取り扱いの **法務確認時期** はいつか (方向性 A 選択時)
- Q-OPS-08: R10 公開 URL の認証層追加 (basic auth or IP 制限) を実装してよいか
- Q-OPS-09: R11 月額コスト上限 (3 AI ツール並走) を **¥10,000 / ¥30,000 / ¥50,000** のどれにするか

---

## 4. 費用感 (現状 + 方向性別)

### 4.1 現状 (2026-05-22 時点)

| 項目 | 月額 | 備考 |
| --- | --- | --- |
| Google AI Pro / Ultra (Gemini) | 既存契約に含む | quota refresh 5/27 18:48 |
| Google Workspace (Sheets / Calendar / Drive) | 既存契約に含む | k-umezawa@ml-mightylink.com |
| GitHub | ¥0 (Free tier) | private repo |
| Anthropic Claude (Claude Code) | ¥0 (1M context 期間利用中) | プロモ枠 |
| OpenAI Codex CLI | ¥0 (ChatGPT plan 利用) | 既存 ChatGPT 契約に含む |
| NotebookLM | ¥0 | Workspace 範囲 |
| **合計** | **追加費用 ¥0** | |

### 4.2 6/2 後シナリオ (方向性別、6/16 〜 9/30 想定)

| シナリオ | API 課金 | Workspace 拡張 | 追加採用 (人件費) | 合計 / 月 |
| --- | --- | --- | --- | --- |
| **A (AI フィット診断)** | Gemini API ¥5,000-¥20,000 + Anthropic API ¥3,000-¥10,000 (本番利用時) | ¥0 (既存内) | 7-8 月以降 営業 1 名検討 | ¥10,000-¥30,000 (人件費除く) |
| **B (Workspace 連携型 PM)** | Gemini API ¥3,000-¥10,000 | Drive 容量 +¥1,000-¥5,000 (顧客データ蓄積) | ¥0 | ¥5,000-¥15,000 |
| **C (PoC 高速構築)** | Gemini API ¥15,000-¥50,000 (案件数比例) + Anthropic API ¥10,000-¥40,000 | ¥0 | 案件 3 社で開発 1 名 | ¥30,000-¥100,000 (人件費除く) |

### 4.3 社長への確認事項

- Q-OPS-10: 6/16 以降の **月次予算枠** は方向性別にいくらまで承認するか
- Q-OPS-11: API 利用量が予算超過しそうな場合、**全停止 / Gemini のみ継続 / 社長承認後継続** のどれをデフォルトにするか
- Q-OPS-12: 顧客からの売上が立つまでの **赤字許容期間** は何ヶ月か

---

## 5. 当日進行 (Operations フェーズ 30 分の内訳)

[DISCUSSION_POINTS の当日進行](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#62-当日進行-90-分想定) の **Operations フェーズ 30 分** に本書を使う:

| 時間 | トピック | 本書のセクション | 確認質問 |
| --- | --- | --- | --- |
| 0-5 分 | 開発体制シナリオ提示 | 1.2 | Q-OPS-01, Q-OPS-02 |
| 5-15 分 | 運用責任分担 | 2.1, 2.2 | Q-OPS-04, Q-OPS-05, Q-OPS-06 |
| 15-25 分 | リスク R9-R13 | 3.2 | Q-OPS-07, Q-OPS-08 |
| 25-30 分 | 費用感 | 4.2 | Q-OPS-09, Q-OPS-10, Q-OPS-11 |

時間が足りない場合は **Q-OPS-09 (月額コスト上限) を最優先**、それ以外は議事録に「保留」で記載して追加面談に持ち越す。

---

## 6. 当日決まらなかった場合のフォロー

各 Q-OPS-xx が 6/2 で保留になった場合の handoff:

| Q-OPS | 保留時の handoff |
| --- | --- |
| Q-OPS-01-03 (体制) | 6/16 定例レビュー (Q-OPS-04 で合意) で再議題化 |
| Q-OPS-04-06 (運用) | Claude Code が暫定案で運用継続、6/16 で確定 |
| Q-OPS-07 (法務) | 寛太が法務 / コンプラに直接問い合わせ、結果を 6/9 までに docs 化 |
| Q-OPS-08 (認証) | Codex レーンが basic auth PoC を 6/9 までに準備、社長確認後に本番反映 |
| Q-OPS-09-12 (費用) | Codex レーンが 6/2-6/16 の実コストを実測、6/16 で再議論 |

---

## 7. 関連 docs と最新化フロー

- 課題管理表 (`data/issues_tracker.tsv` ↔ Google Sheets `課題管理表` タブ) で R9-R13 を追跡。スキーマ [SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md)。
- QA 表 (`data/qa_tracker.tsv` ↔ Google Sheets `QA 表` タブ) に Q-OPS-01〜12 を取り込む (本書から `T606-OPS` カテゴリで起票)。
- 費用感の実測値は Codex レーンが Gemini quota 消費レポートを月次で `docs/COST_REPORT_<YYYY-MM>.md` に出す (6/2 後の新規 WBS タスク)。

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (T606 完遂、12 Q-OPS + 5 新規リスク R9-R13 + 方向性別費用感) |
