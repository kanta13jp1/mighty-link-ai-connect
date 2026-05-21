# NotebookLM Presentation Brief for 2026-06-02 CEO Meeting

Generated: 2026-05-21 22:12:11 UTC+09:00

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
- GitHub Issues #1-#6 track the CEO demo integration backlog.
- NotebookLM source pack was uploaded to Google Docs for source ingestion.
- Notion MCP created an integration evidence page.
- Obsidian vault starter exists locally with `.obsidian` settings.
- Slack post draft exists, while channel and write permission remain pending.
- GitHub Project requires `read:project` / `project` OAuth scope refresh.

## WBS Snapshot

- Total tasks: 61
- Done: 35
- In progress: 3
- Not started: 23
- Completion rate: 57%
- CEO presentation phase tasks: 46
- CEO presentation phase done: 24

## Latest Knowledge-flow / CEO-demo Tasks

- T619: Notion連携 / 仕様・議事録・意思決定DB・バックログ管理のNotion運用設計 / 未着手
- T620: Obsidian連携 / ローカルナレッジ・ADR・プロンプト資産のObsidian運用設計 / 未着手
- T621: 連携デモ導線 / 4ツール連携を社長へ見せる説明順・画面遷移・価値訴求整理 / 完了
- T622: 権限・情報管理 / NotebookLM/Slack/Notion/Obsidian利用時の権限・機密情報ルール整理 / 未着手
- T623: 連携採用判断 / 6/2で決める連携ツール優先順位・導入範囲・責任分担の確認リスト作成 / 完了
- T624: 連携成果物生成 / NotebookLM/Slack/Notion/Obsidianデモ成果物生成スクリプト実装 / 完了
- T625: NotebookLM実体化 / NotebookLM投入用Source Pack生成と想定質問セット作成 / 完了
- T626: Slack実体化 / 社長レビュー向けSlack進捗投稿案の生成 / 完了
- T627: Notion実体化 / Notion用意思決定DB・バックログCSVの生成 / 完了
- T628: Obsidian実体化 / Obsidian vault雛形・ADR・議事録・プロンプトノート生成 / 完了
- T629: 連携UIデモ / 公開デモ/ローカルUIへ開発ナレッジ連携デモセクション追加 / 完了
- T630: 連携APIデモ / FastAPIにKnowledge Flow生成・状態確認APIを追加 / 完了
- T631: 連携成果物検証 / 生成成果物・公開URL・API・Sheets/Calendar同期の総合確認 / 完了
- T632: GitHub Issues連携 / GitHub Issuesに6/2社長デモ向け連携タスクを起票 / 完了
- T633: GitHub Project連携 / GitHub Project board取得・配置のCLI権限確認 / 実行中
- T634: NotebookLM実連携 / NotebookLM投入用Source PackをGoogle Drive/Docsへアップロード / 完了
- T635: Notion実連携 / Notion MCPで社長デモ用の連携証跡ページを作成 / 完了
- T636: Slack連携確認 / Slack CLI/MCPの利用可否と投稿先確認フローを整理 / 完了
- T637: Obsidian実連携 / Obsidian vaultとして開ける設定ファイルを追加 / 完了
- T638: 連携証跡台帳 / CLI/MCP連携の実行結果を社長説明用ドキュメントへ集約 / 完了
- T640: 連携デモリハーサル / NotebookLM/Slack/Notion/Obsidian/GitHubのデモ順を通しで確認 / 未着手
- T642: NotebookLMプレゼン資料化 / NotebookLMでプレゼン資料を作るためのPresentation Brief生成とGoogle Docs化 / 完了
- T643: NotebookLMスライド草案 / NotebookLMへSource PackとPresentation Briefを投入し、8枚以内のプレゼン草案を作る / 未着手
- T646: Slack送信権限確認 / Slack投稿先チャンネルと送信権限を確認し、投稿案を実送信できる状態にする / 未着手

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
