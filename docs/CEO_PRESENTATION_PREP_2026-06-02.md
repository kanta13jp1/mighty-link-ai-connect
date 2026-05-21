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
| CLI/MCP連携証跡 | GitHub Issues、Google Drive/NotebookLM、Notion、Obsidian、Slack確認、GitHub Project権限課題 | T632, T633, T634, T635, T636, T637, T638, T639, T640, T641, T642, T643, T644, T645, T646 |

## 関連ドキュメント

- [CEO_PRESENTATION_DECISION_PACK_2026-06-02.md](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md): スライド構成、判断マトリクス、議事録テンプレート、デモ代替導線。
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
7. Google Docs化したNotebookLM source pack、Notion証跡ページ、GitHub Issues #1-#8 を開く。
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
- Google Drive MCPで `exports/knowledge_flow/notebooklm_source_pack.txt` をGoogle Docsへ変換した。
- Google Drive MCPで `exports/knowledge_flow/notebooklm_presentation_brief.txt` をGoogle Docsへ変換し、NotebookLMでプレゼン資料を作る入力資料を追加した。
- Notion MCPで `Mighty Skill-Bridge CEO Demo Integration Evidence 2026-06-02` を作成した。
- Obsidian vaultに `.obsidian` 設定を追加し、ローカルvaultとして開ける状態に寄せた。
- GitHub Projectは `gh project list` 実行時に `read:project` スコープ不足が判明したため、`T633`, `T641`, Issue #5 で権限復旧タスクとして管理する。
- SlackはローカルCLI未検出かつ送信MCP未露出のため、投稿案と投稿先確認を `T636`, Issue #2 で管理する。
- WBSに `T632` から `T641` を追加し、Sheets/Calendar同期対象にした。

## 2026-05-21 NotebookLMプレゼン資料化の追加

- `exports/knowledge_flow/notebooklm_presentation_brief.md` と `.txt` を生成対象に追加した。
- Google Docs化したNotebookLM Presentation Brief: `https://docs.google.com/document/d/1j_56KN8r_0P1jzJyPE3qVEpuu0O7wwV5O68XRORPoiQ`
- GitHub Issue #7 を起票し、NotebookLMで8枚以内のプレゼン構成・話す要点・想定QAを作るタスクにした。
- GitHub Project OAuth再試行は2分でタイムアウトしたため、Issue #8 と WBS `T644`, `T645` に分離した。
- WBSに `T642` から `T646` を追加した。
