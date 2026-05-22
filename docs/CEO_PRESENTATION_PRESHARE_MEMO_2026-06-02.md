# 6/2 社長打ち合わせ 事前共有メモ + 当日アジェンダ短文 (T614)

作成日: 2026-05-22
オーナー: VSCode + Claude Code レーン
対応 WBS: **T614** 事前送付メモ (5/30-5/31 予定 → 5/22 前倒し完遂)
関連: [DISCUSSION_POINTS](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) (T605) / [QA_PACK](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607) / [OPS_DISCUSSION](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) (T606) / [DECISION_PACK](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md) (T611) / [POST_DECISION_ROADMAP](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) (T615)

---

## このドキュメントの位置づけ

6/2 社長打ち合わせの **3-5 営業日前 (= 5/27 〜 5/30 想定)** に社長へ送る事前共有メモのドラフト。寛太が内容を見て調整した上で、社長へメール (or NotebookLM 経由 or Drive 共有) で送る。

3 種類を用意:
1. **長文版** (社内メール / Drive 共有用) — 当日内容を網羅
2. **短文版** (Slack / モバイル閲覧用) — 50 行以内、5 分で読める
3. **当日アジェンダ短文** (打ち合わせ冒頭 5 分の口頭ガイド) — 寛太が読み上げる

各セクションは社長へ送る前に **寛太が再読・調整** することを前提に、丁寧語で書いてある。

---

## 1. 長文版 (社内メール本文ドラフト)

送付タイミング: 5/27 (火) 〜 5/30 (金)
件名候補: `【6/2 打ち合わせ】判断材料の事前共有 — Mighty Skill-Bridge プロジェクト`

```text
社長

お疲れさまです、寛太です。

6/2 (火) の打ち合わせに向け、判断材料を事前に共有いたします。
当日 90 分の中で社長にご判断いただきたい事項と、こちらでお見せできる
プロトタイプの到達点を以下にまとめております。資料はすべて Google Drive /
Workspace / GitHub で共有可能です。

----

▼ 今回の打ち合わせのゴール (90 分想定)

1. プロトタイプ「Mighty Skill-Bridge」を 3 つの方向性のいずれに育てるかを
   決めること
   - A: AI フィット診断支援 (経歴書 × 案件票のマッチング)
   - B: Workspace 連携型 PM 支援 (WBS / Sheets / Calendar 統合管理)
   - C: AI PoC 高速構築支援 (顧客名差し替えで AI デモを即生成)
   - D: 保留 (5-7 営業日後に追加面談で確定)

2. 最初の対象ユーザー (社内 / 既存顧客 / 見込み顧客) を決めること

3. 6/16 までの 2 週間で最初に作る機能を 1 つ決めること

4. NotebookLM / Slack / Notion / Obsidian の採用優先順位を決めること

5. 月額コスト上限 (現状ほぼゼロ、本格運用で月 1-5 万円想定) を決めること

----

▼ 当日見せられるもの

- 公開デモ URL: https://kanta13jp1.github.io/mighty-link-ai-connect/
  経歴書と案件票を AI が 4 軸 (Skill / Culture / Growth / Performing)
  で評価し、レーダーチャート + 面接質問案を出力します
- Google Sheets 「Mighty-Link AI Connect WBS」
  Phase 1-6 の 80 タスクの進捗、課題管理表 (R1-R14)、想定 QA 表 (35 項目)
- Google Calendar 「Mighty Skill-Bridge 開発計画」
  Phase 6 の作業スケジュールが 6/2 まで埋まっています
- NotebookLM (notebook id: 75521ea6-...)
  docs/ 14 件のドキュメントが投入済、社長向けスライド草案 + Agent Brief 取得済
- PowerPoint プレゼン草案 (Google Drive 上で開けます)
  当日の説明はこちらに沿って進める想定です

----

▼ 当日決めないこと (事前にお知らせ)

- 正式サービス名 (方向性確定後に検討)
- 課金モデル / 本番運用 SLA (方向性確定後に決定)
- 営業資料 / プレスリリース確定版 (方向性確定後 1 週間で起草)

----

▼ 事前にご確認いただけると助かるもの

(任意 — 当日その場で見ても OK です)

1. https://kanta13jp1.github.io/mighty-link-ai-connect/ を一度開いていただき、
   画面の印象とおおまかな操作感を見ておいていただけると、当日の議論が
   スムーズになります
2. 添付の PowerPoint 草案 (8 枚) を流し読みいただけると、当日の説明順
   と論点の輪郭が掴めます
3. 何かこちらから質問しておくべき項目があれば、当日までにお知らせください

----

▼ 当日のお願い

- ノート PC を 1 台ご準備ください (画面共有 / 操作画面の確認用)
- 90 分は確保できる時間で設定をお願いいたします
- 質問は遠慮なくその場でお願いいたします。即答できない場合は議事録に残し、
  6/9 までに回答する運用にいたします

何卒よろしくお願いいたします。

寛太
```

---

## 2. 短文版 (Slack / モバイル閲覧用)

```text
【6/2 打ち合わせ】事前共有

90 分で決めたいこと:
① サービス方向性 (A: AI 診断 / B: PM 支援 / C: PoC 構築 / D: 保留)
② 最初のユーザー (社内 / 顧客)
③ 6/16 までの最優先機能 1 つ
④ 連携ツール採用 (NotebookLM / Slack / Notion / Obsidian)
⑤ 月額コスト上限

当日見せるもの:
- 公開デモ URL (4 軸スコア + レーダーチャート + 面接質問生成)
- Google Sheets (WBS 80 件 / 課題管理表 / QA 表)
- Google Calendar (Phase 6 スケジュール)
- NotebookLM (docs 14 件 + 社長向けスライド草案)
- PowerPoint プレゼン草案 (8 枚)

当日決めないこと: 正式サービス名 / 課金モデル / 本番 SLA

事前確認 (任意):
- https://kanta13jp1.github.io/mighty-link-ai-connect/ をチラ見

質問は当日でも、それ以前にもどうぞ。
```

---

## 3. 当日アジェンダ短文 (打ち合わせ冒頭 5 分の口頭ガイド)

進行役 (寛太) が打ち合わせ冒頭で読み上げる短いオープニング。

```text
本日 90 分でこのプロトタイプを「次に何のサービスに育てるか」を決めたいと
思っています。

進め方は以下のとおりです:

最初の 10 分: 公開デモと現状の到達点をお見せします
次の 30 分: サービス方向性 3 案と対象ユーザーをご判断いただきます
次の 20 分: 最優先機能と AI エンジン選定方針を決めます
次の 10 分: 公開範囲と連携ツール採用を確認します
最後の 10-15 分: 運用・コスト・次回スケジュールを握ります

すべてその場で即決していただく必要はありません。「保留」「追加面談で確定」
も選択肢として用意してあります。即答できない質問は議事録に残して、
6/9 までにこちらから書面で回答する運用にいたします。

それでは、まず公開デモから始めます。
```

---

## 送付方法の選択肢 (D-6 連携ツール採用判断とリンク)

[DISCUSSION_POINTS D-6](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md#d-6-連携ツール採用判断-notebooklm--slack--notion--obsidian) の 6/2 採用判断前の暫定対応:

| 送付方法 | 採否 | 理由 |
| --- | --- | --- |
| **メール** | 採用 | 5/27 までに長文版を送付。最も確実 |
| **Drive 共有 (Google Docs)** | 採用 | 寛太が編集中の状態を見せたい場合の代替 |
| **Slack DM** | **不採用** | Slack live send 未開通 (R3)、6/2 後に採用判断 |
| **Notion 招待** | 不採用 | 社長が Notion ログインを持っているか未確認 |
| **モバイル LINE/Chatwork** | 不採用 | 機密情報を含むため Workspace 内に閉じる |

---

## 添付ファイル候補

事前共有メールに添付する候補 (社長判断で取捨選択):

| ファイル | 添付推奨 | 備考 |
| --- | --- | --- |
| `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` | YES | PowerPoint 8 枚草案 |
| `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` | YES (PDF 化推奨) | 判断マトリクスを 1 枚で見せられる |
| `exports/knowledge_flow/notebooklm_ceo_slide_outline.md` | 任意 | NotebookLM 生成の草案、PPTX で代替可能 |
| `docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md` | NO | 17 論点は当日進行用、事前に渡すと議論を縛る |
| `docs/CEO_PRESENTATION_QA_PACK_2026-06-02.md` | NO | 想定 QA は当日 backstage 用、事前に渡さない |

**PDF 化** が必要な場合は Codex レーンに依頼 (`scripts/generate_ceo_presentation_deck.py` の拡張で `--format pdf` を追加可能)。

---

## 送付前チェックリスト

送付直前に寛太が確認する項目:

- [ ] 公開デモ URL が `Mighty Skill-Bridge` UI を返す (README fallback ではない)
- [ ] PowerPoint が Drive で開ける (`k-umezawa@ml-mightylink.com` 所有)
- [ ] NotebookLM notebook (`75521ea6-...`) が 14 sources Ready
- [ ] Google Sheets `Mighty-Link AI Connect WBS` が最新 ([sync_wbs_to_sheets.py](../scripts/sync_wbs_to_sheets.py) 実行直後)
- [ ] Google Calendar `Mighty Skill-Bridge 開発計画` が 6/2 まで埋まっている
- [ ] 社長のスケジュール確保確認済 (90 分枠)
- [ ] 寛太側でノート PC + ネットワーク + 公開 URL + ローカル FastAPI fallback すべて起動可能
- [ ] 議事録テンプレ ([DECISION_PACK 議事録テンプレート](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#議事録テンプレート)) を `docs/CEO_MEETING_MINUTES_2026-06-02.md` として空ファイル準備済

---

## 送付タイミング案

| 日時 | アクション | 担当 |
| --- | --- | --- |
| **5/27 (水)** | 長文版を社長へメール送付 (PPTX + DECISION_PACK PDF 添付) | 寛太 |
| **5/29 (金)** | 短文版を念のため再送 (前メールが流れた場合の保険) | 寛太 (任意) |
| **6/1 (月)** 21:00 JST | Final Review ([FINAL_REVIEW_CHECKLIST](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md)) 完了確認、6/2 朝の dry-run 準備完了通知 | 寛太 + Codex |
| **6/2 (火)** 朝 | dry-run (25 分以内) | 全員 |
| **6/2 (火)** 当日 | 打ち合わせ冒頭で「当日アジェンダ短文」を読み上げ | 寛太 |

---

## 関連 docs と最新化フロー

- 6/2 打ち合わせ後、本書の「送付タイミング案」セクションは [[feedback-stale-doc-deletion]] により削除候補。
- 当日アジェンダ短文セクションは、6/2 当日の議事録 (`docs/CEO_MEETING_MINUTES_2026-06-02.md`) 内に冒頭引用として転記後、本書から削除。
- 長文版・短文版のメール本文は実際の送付に使った後、本書ではテンプレとしてそのまま残す (次回打ち合わせの参考)。

---

## 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-22 | Claude Code | 初版作成 (T614 完遂、長文版 + 短文版 + 当日アジェンダ短文 + 送付前チェックリスト + 送付タイミング案) |
