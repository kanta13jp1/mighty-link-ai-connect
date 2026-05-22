# 6/2 社長打ち合わせ プレゼン準備ブリーフ

作成日: 2026-05-21

## 前提

6/2 の社長打ち合わせまでは、実際の企画・サービス内容を決め打ちしない。
当日決定するための判断材料、デモ環境、論点、選択肢、次アクションの受け皿を整える。

## 打ち合わせの目的

- 現在のプロトタイプで何が見せられるかを短時間で共有する。
- Google Workspace 連携、WBS管理、公開デモ保護など、開発基盤の到達点を確認する。
- サービス内容・ターゲット・優先機能・6/2以降の開発方針を社長と決定する。
- 未決事項を残したままでも、次のWBS更新に即反映できる状態にする。

## 当日までに用意するもの

| 区分 | 内容 | 対応WBS |
| --- | --- | --- |
| デモ | 公開URL、ローカルFastAPI、Google Sheets WBS、Calendar同期状況 | T602, T603, T608 |
| 説明資料 | 目的、現状、デモ導線、判断ポイント、次アクション、1枚絵サマリー | T604, T610 |
| 論点整理 | サービス内容、対象ユーザー、収益/運用、優先機能、リスク、判断マトリクス | T605, T606, T611 |
| 想定QA | 社長からの質問、回答方針、保留時の扱い | T607 |
| 代替導線 | 公開URL障害時のローカル実行、スクリーンショット、ICS説明 | T613 |
| 事前共有 | 社長へ送る確認ポイント、当日アジェンダの短文ドラフト | T614 |
| 決定後の受け皿 | 議事録、WBS差し替え、Calendar更新、Git反映、決定後ロードマップ枠 | T609, T612, T615 |
| 開発ナレッジ連携 | NotebookLM、Slack、Notion、Obsidian を使った資料要約・通知・議事録・ローカル知識管理の候補整理 | T616, T617, T618, T619, T620, T621, T622, T623 |
| 連携デモ成果物 | NotebookLM投入資料、Slack投稿案、Notion CSV、Obsidian vault、UI/API生成導線 | T624, T625, T626, T627, T628, T629, T630, T631 |
| CLI/MCP連携証跡 | GitHub Issues、Google Drive/NotebookLM、Notion、Obsidian、Slack確認、GitHub Project権限課題、PowerPoint成果物 | T632, T633, T634, T635, T636, T637, T638, T639, T640, T641, T642, T643, T644, T645, T646, T647, T648, T649, T650, T651, T652, T653, T654, T655, T656, T657, T658, T659, T660, T661, T662, T663 |

## 関連ドキュメント

- [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md): スライド構成、判断マトリクス、議事録テンプレート、デモ代替導線。
- [CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md): 17 論点 (D 系 / C 系 / O 系 / X 系) と当日 CEO への確認質問 (T605 deliverable)。
- [CEO_PRESENTATION_QA_PACK_2026-06-02.md](CEO_PRESENTATION_QA_PACK_2026-06-02.md): 22 想定 QA + 保留フロー + 機材チェックリスト (T607 deliverable)。
- [CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md): 開発体制・運用責任分担・リスク R9-R13・費用感 12 Q-OPS (T606 deliverable)。
- [CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md): 方向性 A/B/C/D 別の Phase 7 WBS テンプレ + 共通 Phase 7-common + 議事録 → WBS 反映手順 (T615 deliverable)。
- [CEO_PRESENTATION_PRESHARE_MEMO_2026-06-02.md](CEO_PRESENTATION_PRESHARE_MEMO_2026-06-02.md): 社長への事前共有メモ (長文 / 短文 / 当日アジェンダ短文) + 送付前チェックリスト (T614 deliverable)。
- [CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md): 6/1 21:00 JST Final Review 用 35 項目 checklist (T663 deliverable)。
- [SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md): 課題管理表 + QA表の Sheets スキーマと運用フロー。
- [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md): 3-tool 体制 (Antigravity+Gemini / Codex / Claude Code) と handoff 規約。
- [DEVELOPMENT_KNOWLEDGE_FLOW.md](DEVELOPMENT_KNOWLEDGE_FLOW.md): NotebookLM / Slack / Notion / Obsidian 連携の開発フロー候補。
- [INTEGRATION_DEMO_EVIDENCE_2026-06-02.md](INTEGRATION_DEMO_EVIDENCE_2026-06-02.md): CLI/MCPで実施した連携証跡、GitHub Issues、Project権限課題。
- [WBS.md](WBS.md): WBS詳細とフェーズ別スケジュール。

## 推奨プレゼン構成

1. 今日決めたいこと
2. 現在の到達点
3. 公開デモの確認
4. Google Sheets / Calendar / WBS 管理体制
5. 6/2時点で決めないことと、決めるべきこと
6. サービス内容の選択肢と論点
7. リスク・運用・費用感の確認
8. デモ障害時のバックアップ導線
9. NotebookLM / Slack / Notion / Obsidian の開発フロー候補
10. 決定後の次アクション

## デモ導線

1. 公開URLを開く: `https://kanta13jp1.github.io/mighty-link-ai-connect/`
2. UIが README fallback ではなく、Mighty Skill-Bridge のデモ画面であることを確認する。
3. サンプル経歴書と案件票を読み込み、フィット分析の流れを説明する。
4. Google Sheets の `Mighty-Link WBS`, `WBS Summary`, `WBS Timeline` を見せる。
5. Google Calendar の `Mighty Skill-Bridge 開発計画` を見せる。
6. 画面の「開発ナレッジ連携デモ」で、NotebookLM/Slack/Notion/Obsidian成果物を見せる。
7. Google Docs化したNotebookLM source pack、Notion証跡ページ、GitHub Issues #1-#11/#13/#14/#16 を開く。
8. NotebookLM Presentation Brief を開き、プレゼン資料のたたき台作成はNotebookLMで進める方針を説明する。
9. GitHub Projectは `read:project` / `project` スコープ復旧後に配置することを説明する。
10. 6/2以降、社長決定事項をWBSへ即反映できることを説明する。

## 6/2で決める事項

- このプロトタイプを何のサービスとして育てるか。
- 最初に見せるべき顧客・社内利用者・利用シーン。
- 次に作るべき機能の優先順位。
- Google Workspace連携をどこまで正式運用に寄せるか。
- NotebookLM / Slack / Notion / Obsidian を、6/2以降の開発フローへどの優先順位で組み込むか。
- 社長レビュー後の開発スケジュールと責任分担。

## 6/2までは決め打ちしない事項

- 正式サービス名
- 課金モデル
- 本番運用範囲
- 外部公開範囲
- 最終的な機能セット
- 営業資料・告知文の確定版
- Slack / Notion への自動投稿や外部連携APIの本実装
- NotebookLM / Obsidian への正式な投入範囲

## 想定質問と回答方針

| 質問 | 回答方針 |
| --- | --- |
| これは何のサービスになるのか | 6/2で決める前提。現在は判断材料として、AIマッチング、WBS管理、Google連携、公開デモ保護の到達点を提示する。 |
| どこまで本物のAIなのか | Gemini quota中でも止まらない deterministic fallback を実装済み。Gemini復帰後に structured context を渡す設計にしている。 |
| 公開URLは安全か | root `index.html` の消失を防ぐ Public Demo Guard と GitHub Actions を追加済み。push後も公開URL検証を行う。 |
| WBSは管理しやすいか | CATS型を参考に、階層WBS・集計・タイムラインの3タブ構成へ改善済み。 |
| 打ち合わせ後すぐ何ができるか | 決定事項を `data/WBS.tsv`、Google Sheets、Google Calendar、作業ログへ即反映できる。 |
| NotebookLMやNotionは必須なのか | 必須ではない。6/2時点では、資料要約・議事録・通知・知識管理を速くする候補として比較し、採用/保留/後回しを社長判断に委ねる。 |

**フル版**: 想定 QA 22 件 + 保留フロー + 機材チェックリストは [CEO_PRESENTATION_QA_PACK_2026-06-02.md](CEO_PRESENTATION_QA_PACK_2026-06-02.md) (T607 deliverable) を参照。本表は導入用 simplified 版。

## Risks & Blockers (2026-05-22 時点)

3-tool 体制 ([MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md)) で 6/2 へ向かう過程で識別したリスクと、当日影響を出さないための緩和策を以下にまとめる。詳細チェックは [CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) を参照。

| # | 重要度 | リスク / Blocker | 影響 | 緩和策 | オーナー | 期限 |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | LOW | 未確認の未来モデル名や公開時期がdocsに残る | 社長説明や実装判断が古い前提に引っ張られる | 公式Docsで確認できない未来モデル前提は削除または現在形に置換。`ANTIGRAVITY_GUIDE.md` の該当セクションはT665で削除済み | Codex / Claude | 継続 |
| R2 | HIGH | GitHub `read:project` scope 不足 (Issue #5, #8) | gh CLI で Project ボード操作不可、6/2 デモで Project ボードを見せられない | `gh auth refresh -s project` をブラウザ承認 (人間タスク)。5/27 までに未解決なら **Project ボードを 6/2 デモから除外**、Issues 一覧表示で代替 | 人間 + Codex | 5/27 |
| R3 | MED | Slack CLI / MCP 未露出 ([CODEX_CONTINUATION_NOTES.md:453](CODEX_CONTINUATION_NOTES.md#L453)) | Slack live 送信不可 (T636/T646/T653/T662) | [exports/knowledge_flow/slack_ceo_update.md](../exports/knowledge_flow/slack_ceo_update.md) の草稿表示で代替。live send は約束しない | Codex (草稿維持) / Claude (代替説明準備) | 5/29 |
| R4 | MED | 3 tools 並走で `data/WBS.tsv` の merge 競合 | WBS 行重複・並び順崩壊 | **`data/WBS.tsv` への書き込みは Codex のみ**。Antigravity / Claude は PR コメントで提案 | Codex | 通年 |
| R5 | MED | 5/27 18:48 quota refresh が遅延・失敗 | デモ動画・radar polish が Antigravity で間に合わない | Codex が frontend タスクの静止画 fallback を準備、Antigravity 完成版が無くてもデモ可能な状態を維持 | Codex | 5/27-5/30 |
| R6 | LOW | `requirements.txt` 依存ドリフト | デモ前に dependency 競合で起動失敗 | **5/30 EOD で freeze**、以降 upgrade 禁止。`requirements.txt` を編集する PR は Claude review 必須 | Claude (gate) | 5/30 |
| R7 | LOW | NotebookLM CLI 認証切れ ([notebooklm_cli_next_steps.md](../exports/knowledge_flow/notebooklm_cli_next_steps.md)) | 21 sources の再 sync 不可 | `python scripts/notebooklm_login_workspace.py` を 6/1 dry-run で再確認 | Codex | 6/1 |
| R8 | LOW | サービス方向性 3 選択肢のいずれにも社長が首肯しない | 6/2 結論が出ず、ロードマップ更新不可 | 「保留」を 4th option として明示。決定後の WBS 差し替えフロー (T612) を準備済 | Claude | 6/2 |

**Hard gate**: R1 / R2 / R5 は EOD 5/30 までに緩和策が動いていることを Final Review (6/1 21:00 JST) で確認する。それ以外は劣化シナリオ込みで 6/2 を実施可能。

## 本番前チェック

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/generate_knowledge_flow_demo.py
gh issue list --state all --label ceo-demo
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

## 打ち合わせ後の反映テンプレート

- 決定事項:
- 保留事項:
- 次回までの作業:
- WBS追加/変更:
- Calendar追加/変更:
- Gitコミット:
- 社長共有済みURL:

## 2026-05-21 追加整備

- WBS に `T610` から `T615` を追加し、スライド化素材、判断マトリクス、議事録テンプレート、デモバックアップ、事前送付メモ、決定後ロードマップ枠を管理対象にした。
- `CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` を追加し、6/2当日にサービス内容を決めるための比較表と記録テンプレートを用意した。
- 6/2までは、確定サービス資料ではなく「社長が判断するための資料」として扱う。

## 2026-05-21 開発ナレッジ連携の追加整備

- WBS に `T616` から `T623` を追加し、NotebookLM、Slack、Notion、Obsidian を開発フロー候補として整理した。
- `DEVELOPMENT_KNOWLEDGE_FLOW.md` を追加し、ツール別の役割、入れる情報/入れない情報、6/2で確認すること、セキュリティルールを記録した。
- 6/2まではAPI連携や自動投稿を確定実装せず、社長判断のための資料導線として扱う。

## 2026-05-21 連携デモ実装

- `scripts/generate_knowledge_flow_demo.py` を追加し、NotebookLM投入資料、Slack投稿案、Notion CSV、Obsidian vaultを `exports/knowledge_flow/` へ生成できるようにした。
- FastAPIに `/api/knowledge-flow/generate` と `/api/knowledge-flow/status` を追加した。
- 公開デモ/ローカルUIに「開発ナレッジ連携デモ」セクションを追加した。
- WBSに `T624` から `T631` を追加し、実装済みの連携成果物と検証タスクを管理対象にした。
- 自動投稿や外部API作成は行わず、6/2までは安全な生成物として社長に提示する。

## 2026-05-21 CLI/MCP連携証跡の追加

- GitHub Issuesに `#1` から `#8` を起票し、NotebookLM、Slack、Notion、Obsidian、GitHub Project、WBS連携、プレゼン資料化のタスクを見える化した。
- Google Drive MCPで `exports/knowledge_flow/notebooklm_source_pack.txt` をGoogle Docsへ変換した。2026-05-22にLocal OAuth Drive APIでWorkspace所有Docへ再作成した。
- Google Drive MCPで `exports/knowledge_flow/notebooklm_presentation_brief.txt` をGoogle Docsへ変換し、NotebookLMでプレゼン資料を作る入力資料を追加した。2026-05-22にLocal OAuth Drive APIでWorkspace所有Docへ再作成した。
- Notion MCPで `Mighty Skill-Bridge CEO Demo Integration Evidence 2026-06-02` を作成した。
- Obsidian vaultに `.obsidian` 設定を追加し、ローカルvaultとして開ける状態に寄せた。
- GitHub Projectは `gh project list` 実行時に `read:project` スコープ不足が判明したため、`T633`, `T641`, Issue #5 で権限復旧タスクとして管理する。
- SlackはローカルCLI未検出かつ送信MCP未露出のため、投稿案と投稿先確認を `T636`, Issue #2 で管理する。
- WBSに `T632` から `T641` を追加し、Sheets/Calendar同期対象にした。

## 2026-05-21 NotebookLMプレゼン資料化の追加

- `exports/knowledge_flow/notebooklm_presentation_brief.md` と `.txt` を生成対象に追加した。
- Google Docs化したNotebookLM Presentation Brief: `https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit`
- GitHub Issue #7 を起票し、NotebookLMで8枚以内のプレゼン構成・話す要点・想定QAを作るタスクにした。
- GitHub Project OAuth再試行は2分でタイムアウトしたため、Issue #8 と WBS `T644`, `T645` に分離した。
- WBSに `T642` から `T646` を追加した。

## 2026-05-22 Workspace Google Docs再作成

- Google DocsホームでNotebookLM用資料が見えない状態を解消するため、Google Drive MCPではなく `authorized_user.json` のLocal OAuth Drive APIでGoogle Docsを再作成した。
- 実行アカウントは `python scripts/verify_google_workspace_account.py` で `k-umezawa@ml-mightylink.com` と確認した。
- Source Pack: `https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit`
- Presentation Brief: `https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit`
- Drive APIレスポンスのownerは `k-umezawa@ml-mightylink.com`。証跡は `exports/knowledge_flow/google_drive_workspace_docs.json` に保存した。
- WBSに `T648` を追加し、Sheets/Calendar同期対象にした。

## 2026-05-22 docs配下のNotebookLM同期導線

- `scripts/sync_docs_to_notebooklm.py` を追加し、`docs/*.md` 21件を `k-umezawa@ml-mightylink.com` 所有のGoogle Docsへ同期した。
- 同期manifestは `exports/knowledge_flow/notebooklm_docs_manifest.json` に保存した。
- NotebookLM CLIは `0.3.4` がインストール済み。`scripts/notebooklm_login_workspace.py` で `k-umezawa@ml-mightylink.com` の認証状態を保存した。
- 再実行によりNotebookLMへ21件のsourceを追加し、AIエージェント用の `exports/knowledge_flow/notebooklm_agent_brief.md` と社長説明用の `exports/knowledge_flow/notebooklm_ceo_slide_outline.md` を生成した。
- GitHub Issuesに `#9` と `#10` を追加し、Issue #8へGitHub Projectの `read:project` 不足を再追記した。
- Notion証跡ページ配下に `NotebookLM Docs Sync Evidence 2026-05-22` を作成した: `https://www.notion.so/3671d736b9db8164b46dc143befa29eb`
- WBSに `T649` から `T655` を追加した。

## 2026-05-22 NotebookLM認証完了と社長向け草案取得

- NotebookLM notebook: `75521ea6-6b9b-47b2-9508-50050d8ab2d5`
- title: `Mighty Skill-Bridge Development Knowledge 2026-06-02`
- source: `docs/*.md` 21件すべて `ready`
- AIエージェント向け要約: `exports/knowledge_flow/notebooklm_agent_brief.md`
- 社長向け8枚以内スライド草案: `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- Google Docs化したAgent Brief: `https://docs.google.com/document/d/1W46XIEOj97A-Lp9wfwiDw79RWqB8BGcM04qQjtuJVc4/edit`
- Google Docs化したCEO Slide Outline: `https://docs.google.com/document/d/1xPYZ7ihUklZSm-b3X_LHbxeGvXt6oQXvREgnEX5d0CM/edit`
- JSON証跡: `exports/knowledge_flow/notebooklm_agent_brief.json`, `exports/knowledge_flow/notebooklm_ceo_slide_outline.json`
- WBSは `T643`, `T650`, `T651` を完了に更新し、`T656`, `T657` を追加した。

## 2026-05-22 社長説明用PPTX生成

- NotebookLM CLIで取得したCEO Slide Outlineを元に、`scripts/generate_ceo_presentation_deck.py` でPowerPointを生成した。
- PPTX: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx`
- Google Drive/Slides URL: `https://docs.google.com/presentation/d/1XGHnQHBpJyyhh_Y3I2lq2UThPRC-2dcL/edit?usp=drivesdk&ouid=117190324786156797159&rtpof=true&sd=true`
- サマリー: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.md`
- 生成manifest: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.json`
- 8枚構成: 本日決めたいこと、現在の到達点、Google Workspace基盤、ナレッジ連携実績、NotebookLMからPPTXへ、サービス方向性、運用・リスク、次アクション。
- PPTXは `upload_notebooklm_docs_to_drive.py` のDriveアップロード対象に追加し、`k-umezawa@ml-mightylink.com` 所有ファイルとして扱う。
- WBSは `T658` から `T663` を追加し、PPTX生成、Drive共有、Notion証跡、Issues/Project再追跡、Slack到達性確認、最終パックレビューを管理する。
