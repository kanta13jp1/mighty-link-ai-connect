# Google Sheets 追加タブ スキーマ: 課題管理表 / QA表

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン (スキーマ維持) / 実装は Codex レーン
関連: [WBS_SYNC_GUIDE.md](WBS_SYNC_GUIDE.md) / [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md)

---

## 背景

2026-05-22 にユーザー (kanta13jp@gmail.com) が「スプレッドシートには、WBS の他に、課題管理表、QA表も作成してください。課題や QA が出たらこちらに反映してください」と明示。既存の Sheets 3 タブ (`Mighty-Link WBS` / `WBS Summary` / `WBS Timeline`) に、**`課題管理表`** と **`QA表`** の 2 タブを追加する。

---

## 1. 課題管理表 (Issues Tracker)

### 1.1 正本 / sync 方向

- 正本: [data/issues_tracker.tsv](../data/issues_tracker.tsv)
- sync 方向: TSV → Sheets (`scripts/sync_wbs_to_sheets.py` の同一実行で WBS と一緒に同期)
- 編集: 課題を検知したレーンが `data/issues_tracker.tsv` を append-only で更新 (既存行の変更時は `更新日` を当日に書き換え)
- Sheets タブ名: **`課題管理表`**

### 1.2 カラム定義

| # | カラム | 型 | 必須 | 説明 | 例 |
| --- | --- | --- | --- | --- | --- |
| 1 | `ID` | text | YES | リスク識別子。`R{n}` (既存 Risks)、`OPS-R{n}` (Operations)、`OPSQ-{n}` (Operations QA)、`HANDOFF-{n}` (Codex handoff キュー) など prefix で分類 | `R1`, `OPS-R9`, `HANDOFF-1` |
| 2 | `カテゴリ` | text | YES | `quota`, `auth`, `integration`, `compliance`, `cost`, `infra`, `docs`, `wbs-handoff` から選ぶ | `quota` |
| 3 | `重要度` | enum | YES | `HIGH` / `MED` / `LOW` | `HIGH` |
| 4 | `状態` | enum | YES | `open` / `in_progress` / `resolved` / `wont_fix` / `deferred` | `open` |
| 5 | `タイトル` | text | YES | 1 行サマリ (60 字以内推奨) | `Gemini 3.5 Pro 公開待ち` |
| 6 | `影響` | text | YES | サービス / プレゼンへの影響 | `サービス方向性 pack の品質が Flash 相当に留まる可能性` |
| 7 | `緩和策` | text | YES | 現在進めている対処 | `Claude Code が決定マトリクスを起草、Pro 来れば Antigravity が精緻化` |
| 8 | `オーナー` | text | YES | `Claude` / `Codex` / `Antigravity` / `人間` / `Claude+人間` 等 | `Claude+Antigravity` |
| 9 | `起票日` | date | YES | YYYY-MM-DD | `2026-05-22` |
| 10 | `解決予定日` | date | NO | YYYY-MM-DD、未定なら空欄 | `2026-05-29` |
| 11 | `関連 WBS` | text | NO | `T6xx` 形式、複数なら `,` 区切り | `T605, T611` |
| 12 | `関連 docs` | text | NO | docs/ 内のパス | `docs/CEO_PRESENTATION_PREP_2026-06-02.md` |
| 13 | `関連 Issue` | text | NO | GitHub Issue 番号、複数なら `,` 区切り | `#5, #8` |
| 14 | `メモ` | text | NO | 追加コンテキスト、決定ログ等 | `5/27 までに未解決なら 6/2 デモから Project ボード除外` |
| 15 | `更新日` | date | YES | YYYY-MM-DD、行を編集したときに必ず更新 | `2026-05-22` |

### 1.3 Sheets 装飾 (Codex 実装時の参考)

- ヘッダ行 (Row 1): `Mighty-Link WBS` ヘッダと同じ Mighty Blue (#1A73E8) bg + white text
- 重要度カラム: `HIGH` = `#FCE4D6` (赤系)、`MED` = `#FEF7E0` (黄系)、`LOW` = `#E6F4EA` (緑系)
- 状態カラム: `open` = white、`in_progress` = `#FEF7E0` (黄)、`resolved` = `#E6F4EA` (緑)、`wont_fix` = `#F1F3F4` (灰)、`deferred` = `#E2EFFB` (淡青)
- フィルタは全カラムに自動付与
- 行は `重要度` (HIGH→LOW) → `状態` (open→resolved) → `起票日` (新→古) でソート

### 1.4 既存リスクの初期データソース

- [docs/CEO_PRESENTATION_PREP_2026-06-02.md Risks & Blockers](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点): R1-R8
- [docs/CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md#32-62-後に発生する想定リスク-新規): R9-R13
- [docs/CODEX_CONTINUATION_NOTES.md handoff キュー](CODEX_CONTINUATION_NOTES.md): markdownlint / AGENTS.md / .codex/config.toml / context caching / skills / Antigravity CLI 評価 / JSON hooks PoC / voice transcription 評価

---

## 2. QA表 (QA Tracker)

### 2.1 正本 / sync 方向

- 正本: [data/qa_tracker.tsv](../data/qa_tracker.tsv)
- sync 方向: TSV → Sheets (`scripts/sync_wbs_to_sheets.py` の同一実行で WBS と一緒に同期)
- 編集: QAを検知したレーンが `data/qa_tracker.tsv` を append-only で更新
- Sheets タブ名: **`QA表`**

### 2.2 カラム定義

| # | カラム | 型 | 必須 | 説明 | 例 |
| --- | --- | --- | --- | --- | --- |
| 1 | `ID` | text | YES | QA 識別子。`QA-{nn}` (CEO 想定 QA、QA_PACK 由来)、`Q-OPS-{nn}` (Operations 論点、OPS_DISCUSSION 由来)、`Q-AHOC-{YYYYMMDD}-{n}` (アドホック発生) で分類 | `QA-01`, `Q-OPS-09` |
| 2 | `カテゴリ` | text | YES | `service-direction`, `tech-ai`, `ops`, `cost`, `risk-security`, `integration`, `roadmap`, `ad-hoc` | `service-direction` |
| 3 | `質問` | text | YES | 質問文 (社長 / 顧客から想定 or 実際に聞かれた) | `これは結局、何のサービスになるのか?` |
| 4 | `回答方針` | text | YES | 即答する方針 | `6/2 で決めるため、現時点では確定していない。3 つの方向性を提示する` |
| 5 | `保留時の対応` | text | NO | 即答できないときの handoff | `5-7 営業日以内の追加面談で確定。Codex に POST_CEO_FOLLOWUP 起票依頼` |
| 6 | `関連論点` | text | NO | DISCUSSION_POINTS の `D-1` / `C-2` / `O-3` / `X-1` 等 | `D-1` |
| 7 | `関連 docs` | text | NO | 主要参照 docs | `docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md` |
| 8 | `出典` | text | YES | `想定 (作成日)` または `実問 (誰が・いつ)` | `想定 2026-05-22` or `実問 社長 2026-06-02` |
| 9 | `状態` | enum | YES | `想定済` / `保留中` / `回答済` / `解決不要` | `想定済` |
| 10 | `更新日` | date | YES | YYYY-MM-DD | `2026-05-22` |

### 2.3 Sheets 装飾

- ヘッダ行: 同上 Mighty Blue
- カテゴリカラム: カテゴリ別の淡色 bg (`service-direction` = `#E2EFFB`、`tech-ai` = `#E6F4EA`、`ops` = `#FEF7E0` 等)
- 状態カラム: `想定済` = white、`保留中` = `#FEF7E0`、`回答済` = `#E6F4EA`、`解決不要` = `#F1F3F4`
- フィルタは全カラム
- ソートは `状態` (保留中→想定済→回答済→解決不要) → `カテゴリ` → `ID`

### 2.4 既存 QA の初期データソース

- [docs/CEO_PRESENTATION_QA_PACK_2026-06-02.md](CEO_PRESENTATION_QA_PACK_2026-06-02.md): QA-01 〜 QA-22 (T607 deliverable)
- [docs/CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md): Q-OPS-01 〜 Q-OPS-12 (T606 deliverable)

---

## 3. sync スクリプト実装方針 (Codex レーンへ handoff)

### 3.1 推奨アーキテクチャ

`scripts/sync_wbs_to_sheets.py` を base に、以下 2 タブの同期を同一スクリプトへ統合済み:

```text
scripts/
└── sync_wbs_to_sheets.py        # WBS 3 タブ + 課題管理表 + QA表
```

WBS と tracker を同じ OAuth / Google Workspace アカウント検証で同期することで、実行漏れと誤アカウント同期を避ける。

### 3.2 共通部分の再利用

`sync_wbs_to_sheets.py` の以下のコンポーネントは流用可能:

- OAuth 2.0 認証 (`client_secret.json` → `authorized_user.json` フロー)
- `assert_expected_google_account()` による Workspace アカウント固定 (`k-umezawa@ml-mightylink.com`)
- Mighty-Link カラーパレット (`COLORS` 定数)
- 既存 Sheets ID (`1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8`) の reuse
- API 429 quota 回避ロジック (batch update)

### 3.3 実装時の注意

- 既存 3 タブを **破壊しない** (`worksheet.clear()` の前に existing rows をバックアップ、新タブのみ idempotent な upsert)
- `課題管理表` は **append-only** 思想だが、`状態` カラムの変更は許容 (`更新日` 自動更新)
- `QA表` は ID 安定 (QA-01 は常に同じ行)
- TSV の改行 / タブを含むセル ('回答方針' 等で長文化リスク) は `csv.QUOTE_ALL` で escape

### 3.4 検証

- `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` で `Mighty-Link WBS` / `WBS Summary` / `WBS Timeline` / `課題管理表` / `QA表` を同時更新
- 実行後の Sheets 目視確認 (k-umezawa@ml-mightylink.com で開く)
- 行数が `wc -l data/issues_tracker.tsv` (ヘッダ除く) と一致

---

## 4. 運用フロー (Claude Code セッション中の更新パス)

### 4.1 新規課題発生時

1. Claude Code が `data/issues_tracker.tsv` に新行を append
2. 重要度が `HIGH` で `risk:ceo-blocker` 該当ならば対応 docs (CEO_PRESENTATION_PREP の Risks 表) も同時更新
3. コミット → push → PR → main merge
4. main merge 後に `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` 実行

### 4.2 新規 QA 発生時 (社長 / 顧客から実際に聞かれた)

1. Claude Code が `data/qa_tracker.tsv` に新行 `Q-AHOC-{YYYYMMDD}-{n}` を append
2. 回答方針が確立できる場合は同時に記入、できない場合は `保留中` で先に入れる
3. 保留中 QA は 7 日以内に解消する SLA。解消したら同行を `回答済` に書き換え + `更新日` 更新
4. コミット → push → PR → main merge
5. main merge 後に `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` 実行

### 4.3 既存課題 / QA の状態変更

1. `data/issues_tracker.tsv` / `data/qa_tracker.tsv` の該当行を直接編集 (状態 + 更新日のみ)
2. 同上 commit → push → PR → main → sync

---

## 5. 制約事項

- 個人情報 / 認証情報 / API キーは絶対に tracker に記入しない (Sheets は社長共有のため、Workspace 内とはいえ Issue 名にのみ抽象化)
- `data/WBS.tsv` の直接編集は Codex レーンを正とする。
- `data/issues_tracker.tsv` / `data/qa_tracker.tsv` は、課題やQAを検知したレーンが更新してよい。ただし1行1件、ID安定、`更新日` 更新、秘密情報禁止を守る。

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (課題管理表 + QA表 スキーマ定義、sync スクリプト実装方針、運用フロー) |
| 2026-05-22 | Codex | `sync_wbs_to_sheets.py` に `課題管理表` / `QA表` 同期を統合し、同一OAuth実行で5タブを更新する運用へ変更 |
