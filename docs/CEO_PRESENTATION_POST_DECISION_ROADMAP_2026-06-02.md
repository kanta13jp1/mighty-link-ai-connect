# 6/2 決定後ロードマップ枠 (T615)

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン
対応 WBS: **T615** 決定後ロードマップ枠 (6/1-6/2 予定 → 5/22 前倒し完遂)
関連: [DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (T605) / [QA_PACK](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607) / [OPS_DISCUSSION](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) (T606) / [DECISION_PACK](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) (T611)

---

## このドキュメントの位置づけ

2026-06-02 社長打ち合わせ後に「どの方向性が選ばれても 24 時間以内に Phase 7 WBS を起こせる」状態を作るための **テンプレ集**。

社長が方向性 A / B / C / D (保留) のどれを選んでも、本書の該当セクションを `data/WBS.tsv` の Phase 7 行として差し込むだけで実装に移れる。

進行役 (Codex/人間) は 6/2 打ち合わせ直後に [議事録テンプレ](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#議事録テンプレート) の `1. 決定事項 - サービス方向性` を確認 → 本書の対応セクション 1 つを `data/WBS.tsv` へ flip し、`sync_wbs_to_sheets.py` / `sync_wbs_to_calendar.py` を実行。

---

## 共通: 全方向性で着手するタスク (Phase 7-common)

方向性決定によらず即着手するもの。6/2 打ち合わせ翌日 (6/3) 朝までに WBS へ起票:

| ID 案 | タスク名 | 担当 | 期間 | 備考 |
| --- | --- | --- | --- | --- |
| T701 | 6/2 議事録 docs 化 + Notion 投入 | Claude | 6/2 18:00 - 6/3 12:00 | `docs/CEO_MEETING_MINUTES_2026-06-02.md` 起票 |
| T702 | 決定事項を WBS Phase 7 へ反映 | Codex | 6/3 12:00 - 6/3 18:00 | 本書の対応セクションを `data/WBS.tsv` へ flip |
| T703 | Phase 7 用 Calendar イベント起票 | Codex | 6/3 18:00 - 6/4 09:00 | `sync_wbs_to_calendar.py` 実行 |
| T704 | NotebookLM に Phase 7 docs を投入 | Codex | 6/4 - 6/5 | `sync_docs_to_notebooklm.py` 再実行 |
| T705 | 6/16 定例レビュー Calendar 招待作成 (Q-OPS-04 が YES の場合) | 人間 | 6/3 - 6/4 | 隔週 30 分枠 |
| T706 | R9 法務確認 (方向性 A 選択時) / R10 認証層 PoC (方向性 A/C 選択時) | 人間 + Codex | 6/3 - 6/9 | [OPS_DISCUSSION Q-OPS-07/08](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) 参照 |
| T707 | R11 月額コスト実測レポート 1 週目 | Codex | 6/3 - 6/9 | `docs/COST_REPORT_2026-06.md` 新規 |
| T708 | サービス方向性決定の Slack/Notion/メール通知 (採用ツール次第) | Claude + 人間 | 6/2 21:00 - 6/3 09:00 | D-6 採用判断後の通知運用 |

---

## 方向性 A: AI フィット診断支援 (Phase 7-A)

[DISCUSSION_POINTS D-1 選択肢 A](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-1-サービス方向性) を CEO が選んだ場合の WBS テンプレ。

### 目標 (6/3 - 6/16)

社内パイロット (人材担当 + 営業 1 名ずつ計 2 名) で経歴書 × 案件票の AI フィット診断を回す。

### Phase 7-A WBS テンプレ

| ID 案 | タスク名 | 担当 | 期間 | 備考 |
| --- | --- | --- | --- | --- |
| T710 | 利用同意書テンプレ起票 (R9 対応) | 人間 + Claude | 6/3 - 6/9 | 個人情報 / コンプラ法務確認 |
| T711 | 社内パイロット参加者の選定・依頼 | 人間 | 6/3 - 6/6 | 人材担当 1 名 / 営業 1 名 |
| T712 | AI スコア根拠の UI 化 (`matched_skills` / `missing_skills` / 4 軸根拠を視覚化) | Antigravity (UI) + Codex (API) | 6/3 - 6/13 | [QA-07 D-3 選択肢 A](CEO_PRESENTATION_QA_PACK_2026-06-02.md#qa-07) |
| T713 | サンプル経歴書 5 件 / サンプル案件票 5 件を Workspace に準備 | 人間 | 6/3 - 6/9 | 個人情報マスキング済を使用 |
| T714 | 案件候補ストック管理 UI (複数案件 × 複数エンジニアの突合ビュー) | Antigravity | 6/9 - 6/13 | [D-3 選択肢 B](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-3-最優先機能-62--616-の-2-週間で作るもの) |
| T715 | 公開 URL 認証層 (basic auth) 実装 (R10 対応) | Codex | 6/3 - 6/9 | [Q-OPS-08](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) |
| T716 | パイロット結果サマリ docs 化 | Claude | 6/13 - 6/16 | `docs/PILOT_REPORT_2026-06-16.md` 新規 |
| T717 | 6/16 定例レビュー 用ダッシュボード起票 | Codex | 6/13 - 6/16 | Sheets `パイロット集計` タブ |

### 想定リスク (Phase 7-A 特有)

- 個人情報を含む経歴書の Workspace 内クローズ運用が法務確認まで停止する場合あり (R9)
- 案件票の質が AI スコア精度を左右する → サンプル案件票 5 件のクオリティが鍵
- 社内パイロット 2 名のスケジュール確保が課題

---

## 方向性 B: Workspace 連携型 PM 支援 (Phase 7-B)

[DISCUSSION_POINTS D-1 選択肢 B](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-1-サービス方向性) を CEO が選んだ場合の WBS テンプレ。

### 目標 (6/3 - 6/16)

マイティ・リンク社内の WBS / 進捗 / カレンダー管理を本サービス内で自走できる状態にする (社長が Sheets を直接見なくても本 UI で把握できる)。

### Phase 7-B WBS テンプレ

| ID 案 | タスク名 | 担当 | 期間 | 備考 |
| --- | --- | --- | --- | --- |
| T720 | WBS UI 内製化 ([O-1](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#o-1-wbs-ui-内製化)) | Antigravity + Codex | 6/3 - 6/13 | 本 UI 内に WBS 階層・進捗・タイムライン表示 |
| T721 | Sheets 進捗の双方向 sync (現状は TSV → Sheets の片方向、双方向化) | Codex | 6/3 - 6/13 | Sheets で編集 → TSV 反映 / 逆方向 |
| T722 | Calendar イベントクリック → 本 UI のタスク詳細遷移 | Antigravity | 6/9 - 6/13 | Antigravity Browser Agent 経由 |
| T723 | 社長向け週次レポート自動生成 (Q-OPS-04 隔週レビューに直結) | Codex | 6/9 - 6/16 | Gemini 3.5 Flash で `docs/WEEKLY_REPORT_<YYYY-MM-DD>.md` 自動生成 |
| T724 | 既存顧客 1 社の PM フロー試行 (要・別途同意) | 人間 + Codex | 6/9 - 6/16 | 社長判断後に営業 |
| T725 | NotebookLM に WBS スナップショットを週次 sync | Codex | 6/3 - 6/16 | 既存 `sync_docs_to_notebooklm.py` の Phase 7 拡張 |
| T726 | 6/16 定例レビュー UI 動線完成 | Antigravity | 6/13 - 6/16 | 30 分で社長確認が終わる導線 |

### 想定リスク (Phase 7-B 特有)

- Sheets 双方向 sync は競合解消が複雑 (Codex の write 排他規約 R4 を維持できるか)
- 社長が Sheets を直接見たい場合は内製化価値が薄い → Q-OPS-06 で「レビュー粒度」の合意必須

---

## 方向性 C: AI PoC 高速構築支援 (Phase 7-C)

[DISCUSSION_POINTS D-1 選択肢 C](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-1-サービス方向性) を CEO が選んだ場合の WBS テンプレ。

### 目標 (6/3 - 6/16)

顧客名を差し替えるだけで AI デモを 1 日で出力できるテンプレート機能。最初の見込み顧客 1 社に提案できる状態。

### Phase 7-C WBS テンプレ

| ID 案 | タスク名 | 担当 | 期間 | 備考 |
| --- | --- | --- | --- | --- |
| T730 | 顧客名 / 業界 / 想定 KPI を差し替える PoC テンプレ ([D-3 選択肢 F](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-3-最優先機能-62--616-の-2-週間で作るもの)) | Codex + Antigravity | 6/3 - 6/13 | `scripts/generate_poc_demo.py --client X --industry Y` |
| T731 | 業界別サンプルデータ 3 セット (人材 / 営業 / SaaS) | 人間 + Codex | 6/3 - 6/9 | `data/poc_samples/<industry>.json` |
| T732 | 公開 URL 認証層 + 顧客別サブパス (R10 対応 + customer isolation) | Codex | 6/3 - 6/13 | `https://.../poc/<client-slug>/` 形式 |
| T733 | PoC 提案資料の自動生成 (PPTX) | Codex | 6/9 - 6/16 | 既存 `generate_ceo_presentation_deck.py` の汎用化 |
| T734 | 見込み顧客 1 社の選定・初回提案 | 人間 | 6/9 - 6/16 | 営業 / 社長判断 |
| T735 | PoC コスト実測 (API 利用 / 工数) | Codex | 6/9 - 6/16 | `docs/POC_COST_<YYYY-MM-DD>.md` |
| T736 | 開発 1 名追加採用判断 (顧客 3 社同時パイロット閾値) | 人間 | 6/9 - 6/16 | [Q-OPS-02](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) |

### 想定リスク (Phase 7-C 特有)

- 汎用化しすぎて価値がぼやける (DECISION_PACK 判断マトリクスの「主なリスク」)
- 顧客名差し替え機能は customer-specific データを漏らさない検証が必須 (cross-tenant 防御)
- 月額コストが案件数比例で急増 (R11、Q-OPS-09 上限内に収まるか実測)

---

## 方向性 D: 保留 (5-7 営業日以内の追加面談で再決定)

CEO が 6/2 で即決しない場合の handoff。

### 即着手するもの

| ID 案 | タスク名 | 担当 | 期間 | 備考 |
| --- | --- | --- | --- | --- |
| T740 | 追加面談の日程調整 (6/9 までに 30-60 分枠) | 人間 | 6/2 21:00 - 6/3 12:00 | 社長スケジュール優先 |
| T741 | 6/2 で出た保留事項 ([議事録テンプレ 2. 保留事項](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#議事録テンプレート)) を `docs/POST_CEO_FOLLOWUP_2026-06-XX.md` に整理 | Claude | 6/3 09:00 - 6/3 18:00 | QA_PACK の「当日の保留フロー」適用 |
| T742 | 追加面談用 1 ページ判断材料 (差分のみ) | Claude | 6/3 - 6/6 | 既存 docs と重複しない範囲 |
| T743 | 追加面談議事録 docs 化 + 方向性確定 | Claude + 人間 | 追加面談当日 - 翌日 | 確定後は T720/T730/T710 のいずれかへ |

### 暫定運用 (方向性確定までの 1 週間)

- 既存 deterministic fallback の品質維持 (Codex)
- docs / WBS の現状維持 (Claude / Codex)
- 新規実装は **凍結** (5/30 freeze ルール R6 に類似)
- Best Practices Refresh は通常通り継続 (公式 docs fetch 毎セッション)

---

## 議事録 → WBS 反映の具体手順 (Codex 担当)

6/2 議事録テンプレで「サービス方向性 = X」が確定したら、Codex セッションで以下を実行:

1. 本書の `Phase 7-X` セクションの WBS テンプレを `data/WBS.tsv` に append
2. 共通 Phase 7-common (T701-T708) も同時に追加
3. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` を実行 → Sheets `Mighty-Link WBS` + `課題管理表` + `QA表` を同期
4. `python scripts/sync_wbs_to_calendar.py` を実行 → Calendar に Phase 7 イベント起票
5. `python scripts/sync_docs_to_notebooklm.py` を実行 → NotebookLM source 更新
6. `git add data/WBS.tsv docs/CEO_MEETING_MINUTES_2026-06-02.md && git commit -m "[codex] feat: phase 7 WBS for direction X" && git push`
7. `gh pr create + gh pr merge --squash` で main 反映 → ([[feedback-session-commit-push-merge]] 準拠)

実行記録は [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md) の「2026-06-02 (post-CEO meeting)」セクションに残す。

---

## 関連 docs と最新化フロー

- 本書は 6/2 までは **テンプレ集** として扱う。6/2 確定後は不要セクション (例: 方向性 A 採用なら B/C/D セクション) を **本書から削除** ([[feedback-stale-doc-deletion]] 準拠)。
- 採用された方向性のセクションは `data/WBS.tsv` に flip された時点で WBS の正本に移管、本書からは要約のみ残す。

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (T615 完遂、方向性 A/B/C/D の Phase 7 WBS テンプレ + Phase 7-common + 議事録 → WBS 反映手順) |
