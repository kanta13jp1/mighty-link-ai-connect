# NotebookLM Presentation Brief for 2026-06-02 CEO Meeting

Generated: 2026-05-22 22:46:49 UTC+09:00

## How to use this in NotebookLM

Upload this document together with:

- `notebooklm_source_pack.txt`
- `docs/CEO_PRESENTATION_PREP_2026-06-02.md`
- `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md`
- `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md`
- `data/WBS.tsv`

Then ask NotebookLM to generate a CEO-ready presentation outline, speaker notes,
and likely executive questions. Do not upload credentials or personal data.

## Presentation Objective

The 2026-06-02 meeting should not finalize the service content before discussion.
It should help the CEO decide the service direction, first user, priority feature,
and which development knowledge-flow tools should become official.

## Current Evidence to Show

- Public demo remains guarded by Public Demo Guard and GitHub Pages deployment.
- WBS is synced to Google Sheets and Google Calendar.
- GitHub Issues #1-#11/#13/#14/#16 track the CEO demo integration backlog.
- NotebookLM source pack was uploaded to Google Docs for source ingestion.
- NotebookLM CLI is authenticated as the Workspace account and generated an agent brief plus CEO slide outline.
- CEO PowerPoint deck was generated from the NotebookLM slide outline.
- Notion MCP created an integration evidence page.
- Obsidian vault starter exists locally with `.obsidian` settings.
- Slack post draft exists, while channel and write permission remain pending.
- GitHub Project requires `read:project` / `project` OAuth scope refresh.

## WBS Snapshot

- Total tasks: 89
- Done: 65
- In progress: 5
- Not started: 19
- Completion rate: 73%
- CEO presentation phase tasks: 74
- CEO presentation phase done: 54

## Latest Knowledge-flow / CEO-demo Tasks

- T632: GitHub Issues連携 / GitHub Issuesに6/2社長デモ向け連携タスクを起票 / 完了
- T633: GitHub Project連携 / GitHub Project board取得・配置のCLI権限確認 / 実行中
- T634: NotebookLM実連携 / NotebookLM投入用Source PackをGoogle Drive/Docsへアップロード / 完了
- T635: Notion実連携 / Notion MCPで社長デモ用の連携証跡ページを作成 / 完了
- T636: Slack連携確認 / Slack CLI/MCPの利用可否と投稿先確認フローを整理 / 完了
- T637: Obsidian実連携 / Obsidian vaultとして開ける設定ファイルを追加 / 完了
- T638: 連携証跡台帳 / CLI/MCP連携の実行結果を社長説明用ドキュメントへ集約 / 完了
- T640: 連携デモリハーサル / NotebookLM/Slack/Notion/Obsidian/GitHubのデモ順を通しで確認 / 未着手
- T642: NotebookLMプレゼン資料化 / NotebookLMでプレゼン資料を作るためのPresentation Brief生成とGoogle Docs化 / 完了
- T643: NotebookLMスライド草案 / NotebookLMへSource PackとPresentation Briefを投入し、8枚以内のプレゼン草案を作る / 完了
- T646: Slack送信権限確認 / Slack投稿先チャンネルと送信権限を確認し、投稿案を実送信できる状態にする / 未着手
- T648: Workspace Google Docs再作成 / NotebookLM用Google Docsをk-umezawa@ml-mightylink.com所有で再作成 / 完了
- T650: NotebookLM CLI認証復旧 / NotebookLM CLIをk-umezawa@ml-mightylink.comで再認証 / 完了
- T651: NotebookLM Agent Brief取得 / NotebookLMの要約をAIエージェント開発入力として保存 / 完了
- T653: Slack連携実送信準備 / Slack送信ツール・投稿先チャンネル・社長共有範囲の確定 / 未着手
- T654: Notion証跡更新 / NotebookLM docs同期結果をNotion証跡ページ配下に追加 / 完了
- T655: Obsidian Agent Brief導線 / Obsidian vaultにNotebookLM Agent Brief参照導線を追加 / 完了
- T656: NotebookLM補助ログイン導線 / NotebookLM CLIのログイン保存を補助するWorkspace専用スクリプト作成 / 完了
- T657: NotebookLM社長スライド草案取得 / NotebookLMからCEO向け8枚以内のプレゼン草案を取得して保存 / 完了
- T658: NotebookLM PowerPoint化 / NotebookLM CLIで取得したCEO Slide Outlineを社長説明用PowerPointへ変換 / 完了
- T660: Notion PPTX証跡更新 / Notion MCPでPPTX生成・Drive共有・残課題を証跡ページへ記録 / 完了
- T662: Slack MCP/CLI到達性証跡 / Slack CLIと送信MCPの利用可否を確認し、投稿案と残課題を整理 / 完了
- T663: 6/2資料最終パックレビュー / PPTX、NotebookLM資料、WBS、Calendar、Issue、Notion証跡を通しで確認 / 未着手
- T664: 三ツール開発フロー整備 / Antigravity + Gemini / VSCode + Codex / VSCode + Claude Codeの役割と毎セッション運用ルールを共有手順へ固定 / 完了

## Recommended Slide Story

1. Why we are meeting on 2026-06-02: decide direction, not lock details early.
2. What is already working: public demo, WBS, Google Workspace sync, guardrails.
3. What changed this week: NotebookLM / Slack / Notion / Obsidian workflow proof.
4. How NotebookLM helps: source reading, Q&A generation, presentation drafting.
5. How GitHub Issues/Project should help: task visibility and implementation trace.
6. What is still pending: GitHub Project OAuth scope and Slack destination/channel.
7. Decisions needed from CEO: service direction, first audience, workflow tools.
8. Immediate next actions after the meeting: update WBS, Calendar, Issues, docs.

## NotebookLM Prompts for Presentation Creation

1. この資料群をもとに、社長向け10分プレゼンの構成を8枚以内で作ってください。
2. 各スライドについて、見出し、話す要点、見せる証跡URL、社長に聞く質問を作ってください。
3. 6/2時点で決めるべきことと、まだ決めない方がよいことを分けてください。
4. GitHub ProjectとSlackが未完了である点を、ネガティブではなく次の実行タスクとして説明してください。
5. プレゼン後にWBSへ追加すべきタスク候補を、優先順位つきで出してください。

## Speaker Notes Draft

The core message is: the product direction is intentionally undecided until the
CEO meeting, but the development operating system is already becoming visible.
Codex, Google Workspace, GitHub Issues, Notion, Obsidian, and NotebookLM can
work together so that decisions made on 2026-06-02 become WBS, Calendar, Issues,
and documentation updates immediately.
