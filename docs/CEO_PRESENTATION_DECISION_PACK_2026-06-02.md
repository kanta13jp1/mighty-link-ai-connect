# 6/2 社長打ち合わせ 判断材料パック

作成日: 2026-05-21

## 位置づけ

この資料は、6/2 の社長打ち合わせで企画・サービス内容を決定するための判断材料です。
6/2 以前にサービス内容を確定させるものではなく、公開デモ、WBS、Google Workspace 連携、開発体制を見ながら、当日に意思決定しやすくするための下準備として扱います。

## 当日のゴール

- 現在のプロトタイプで見せられる価値を短時間で共有する。
- サービス方向性、対象ユーザー、最優先機能を社長と決める。
- 6/2 以降に更新する WBS、Calendar、Git 運用の入口を明確にする。
- 決めない事項と保留事項を分け、次回までのアクションに落とす。

## プレゼン構成案

| # | スライド | 伝えること | 対応WBS |
| --- | --- | --- | --- |
| 1 | 本日決めたいこと | 企画確定ではなく、方向性・優先順位・次アクションを決める場であること | T601, T610 |
| 2 | 現在の到達点 | 公開デモ、FastAPI、AI fallback、Sheets/Calendar 連携、公開URLガード | T603, T610 |
| 3 | 公開デモ | 経歴書/案件票からフィット診断へ進む体験を見せる | T602 |
| 4 | 管理基盤 | CATS型WBS、Summary、Timeline、Calendar同期で進捗管理できること | T603 |
| 5 | AI復帰時の伸びしろ | Gemini quota 回復後に structured context を渡して精度改善できること | T304, T305 |
| 6 | 方向性の選択肢 | 複数案を比較し、当日決める判断軸を提示する | T605, T611 |
| 7 | 運用・体制論点 | 誰が使うか、誰が更新するか、どこまで公開するか | T606 |
| 8 | リスクと対策 | 公開URL、認証、Google API、デモ障害時のバックアップ | T607, T613 |
| 9 | 決定後の反映方法 | 議事録から WBS / Calendar / Git へ即時反映する流れ | T609, T612 |
| 10 | 開発ナレッジ連携 | NotebookLM / Slack / Notion / Obsidian をどう使うか | T616, T617, T621, T623 |
| 11 | 連携成果物デモ | NotebookLM投入資料、Slack投稿案、Notion CSV、Obsidian vaultを見せる | T624, T625, T626, T627, T628, T629, T630 |
| 12 | CLI/MCP実連携証跡 | Google Drive、Notion、GitHub Issues、Project権限課題、Slack到達点を見せる | T632, T633, T634, T635, T636, T637, T638, T639 |
| 13 | 社長への確認事項 | 決定してほしい項目、保留してよい項目、次回までの宿題 | T614, T615, T622, T631, T640, T641 |

## 判断マトリクス

| 判断軸 | 方向性A: AIフィット診断支援 | 方向性B: Workspace連携型PM支援 | 方向性C: AI PoC高速構築支援 |
| --- | --- | --- | --- |
| 想定利用者 | 営業、人材担当、エンジニア | 経営、PM、現場責任者 | 新規事業、営業企画、開発責任者 |
| 見せやすいデモ | 経歴書と案件票のマッチング結果 | WBS、Sheets、Calendarの同期管理 | 短期間でAIデモを形にする流れ |
| 現プロトタイプとの親和性 | 高い | 高い | 中から高い |
| 6/2以降の初期実装 | スコア根拠、質問生成、案件候補管理 | WBS更新、社長レビュー、進捗可視化 | テンプレート化、デモ生成手順化 |
| 価値の説明しやすさ | 採用・SES・案件配属の効率化 | 経営報告と進捗管理の高速化 | 顧客提案速度と検証回数の増加 |
| 主なリスク | 入力データ品質、AI精度、個人情報 | 運用定着、権限管理、更新責任 | 汎用化しすぎて価値がぼやける |
| 6/2で決めたいこと | 最初の対象業務と評価指標 | 誰の管理業務に適用するか | どの顧客/案件でPoC化するか |

## 開発ナレッジ連携の判断材料

| ツール | 6/2までの位置づけ | 社長に見せる価値 | 確認したい判断 |
| --- | --- | --- | --- |
| NotebookLM | 資料要約・想定QA生成の候補 | 社長説明前に `docs/` とWBSを読み込み、論点を短時間で掴める | 社長向け説明準備に使うか |
| Slack | 進捗通知・レビュー依頼・同期結果共有の候補 | WBS同期、GitHub Actions、公開URL検証の結果を短文で追える | 通知先チャンネルと共有範囲 |
| Notion | 議事録・意思決定DB・バックログ管理の候補 | 6/2決定事項から次アクションまで一元管理できる | 公式台帳にするか |
| Obsidian | ローカル思考メモ・ADR・プロンプト資産管理の候補 | 未整理の設計判断を溜め、公式化する内容だけ `docs/` へ昇格できる | 個人メモ運用に限定するか |

詳細は [DEVELOPMENT_KNOWLEDGE_FLOW.md](DEVELOPMENT_KNOWLEDGE_FLOW.md) にまとめる。

## 実装済み連携デモ成果物

| 対象 | 生成物 | 説明 |
| --- | --- | --- |
| NotebookLM | `exports/knowledge_flow/notebooklm_source_pack.md` / `exports/knowledge_flow/notebooklm_source_pack.txt` | `docs/` とWBSをまとめた投入用資料。TXT版はGoogle Docs化済み。 |
| Slack | `exports/knowledge_flow/slack_ceo_update.md` | 社長レビュー前に投稿できる進捗共有文案。 |
| Notion | `exports/knowledge_flow/notion_decision_log.csv` | 意思決定DBとして取り込めるCSV。 |
| Notion | `exports/knowledge_flow/notion_backlog_import.csv` | WBS連携バックログとして取り込めるCSV。 |
| Obsidian | `exports/knowledge_flow/obsidian_vault/` | ADR、議事録、プロンプトを含むローカルvault雛形。 |
| UI/API | 公開デモの「開発ナレッジ連携デモ」 / `/api/knowledge-flow/generate` | 画面から成果物の存在を説明し、ローカルでは再生成できる。 |
| 連携証跡 | `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md` | Google Docs、Notionページ、GitHub Issues、Project/Slackの残課題を説明する。 |

このデモは、秘密情報を含まない範囲で外部連携の到達点も見せる。Slack投稿とGitHub Project配置は、投稿先・権限が整ってから正式化する。

## CLI/MCP実連携の見せ方

| 連携先 | 見せるもの | 補足 |
| --- | --- | --- |
| Google Drive / NotebookLM | https://docs.google.com/document/d/1J3spIzQTq5eZ2RGx6K_knt6I3c0GtPDMPhKfBGwnMvI | MarkdownはDrive変換対象外だったため、TXT版を生成してGoogle Docs化した。 |
| Notion | https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951 | 6/2社長デモ用の連携証跡ページ。 |
| GitHub Issues | https://github.com/kanta13jp1/mighty-link-ai-connect/issues | Issue #1-#6で連携タスクを管理。 |
| GitHub Project | Issue #5 / WBS `T633`, `T641` | `gh` tokenの `read:project` スコープ復旧後にProjectへ配置。 |
| Slack | `exports/knowledge_flow/slack_ceo_update.md` | 送信先チャンネルと共有範囲を6/2に確認。 |

## 当日質問リスト

- 最初に解決したい業務課題は、営業支援、人材管理、PM支援、顧客提案のどれか。
- 社長が最初に見せたい相手は、社内、既存顧客、見込み顧客のどれか。
- 6/2 以降の2週間で、デモ品質、AI精度、運用基盤、資料化のどれを優先するか。
- Google Workspace 連携は、社内運用前提か、顧客提示価値の一部にするか。
- 公開URLの扱いは、社長共有のみ、社内共有、外部共有のどこまで許容するか。
- NotebookLM / Slack / Notion / Obsidian のうち、6/2以降に正式導入する優先順位はどれか。
- SlackやNotionに社長確認事項を流す場合、どの範囲まで共有してよいか。
- Obsidianを個人開発メモに限定し、公式情報は `docs/` / Notion / Google Docs に戻す運用でよいか。

## 議事録テンプレート

```text
日時:
参加者:

1. 決定事項
- サービス方向性:
- 対象ユーザー:
- 優先機能:
- 公開範囲:
- 次回確認日:

2. 保留事項
- 

3. 次アクション
- WBS追加/変更:
- Calendar追加/変更:
- Git更新:
- 社長共有資料:

4. 6/2以降の作業メモ
- 
```

## デモ障害時の代替導線

1. 公開URLが不安定な場合は、ローカル `python src/app.py` と `http://localhost:8000` で見せる。
2. Google Sheets が開けない場合は、`data/WBS.tsv` と `docs/WBS.md` で構成を説明する。
3. Calendar同期が見えない場合は、`exports/mighty_development_plan.ics` と同期ログで補足する。
4. Gemini quota が残っていない場合は、deterministic fallback の構造化結果を見せ、Gemini復帰後の差し替え方針を説明する。

## 当日前チェックコマンド

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
gh issue list --state all --label ceo-demo
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```
