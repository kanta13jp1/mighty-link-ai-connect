# 開発ナレッジ連携フロー手順書

作成日: 2026-05-21

## 目的

NotebookLM、Slack、Notion、Obsidian を開発フロー候補として整理し、6/2 の社長打ち合わせで「どこまで導入するか」「誰が使うか」「どの情報を流すか」を判断できる状態にする。

6/2 までは、実際の企画・サービス内容や正式運用範囲を決め打ちしない。ここでは、Mighty Skill-Bridge の開発・報告・意思決定を速くするための情報導線として扱う。

## 基本方針

- GitHub と `docs/` をコード・公式手順・変更履歴の主ソースにする。
- Google Sheets / Calendar は WBS、進捗、日程の主ソースにする。
- NotebookLM は社長説明前の資料読み込み・質問生成・要約支援の候補にする。
- Slack は進捗通知、レビュー依頼、短い意思決定ログの候補にする。
- Notion は議事録、意思決定DB、バックログ、社長レビュー用ページの候補にする。
- Obsidian はローカルの思考メモ、ADR、プロンプト資産、未整理アイデアの候補にする。
- 認証情報、個人情報、未承認の顧客情報は、外部サービスへ投入しない。

## ツール別の役割

| ツール | 主な役割 | 入れる情報 | 入れない情報 | 6/2で確認すること |
| --- | --- | --- | --- | --- |
| NotebookLM | 社長説明前の資料要約、質問生成、論点抽出 | `docs/` の手順書、WBS、判断材料パック | 認証JSON、個人情報、未承認顧客情報 | 社長向け説明準備に使うか |
| Slack | 日次進捗、レビュー依頼、障害/同期完了通知 | WBS更新、GitHub Actions結果、同期結果サマリー | 秘密鍵、全文ログ、未確認の個人データ | どのチャンネルに何を流すか |
| Notion | 議事録、意思決定DB、バックログ、社長レビュー資料 | 6/2決定事項、タスク、保留事項、ロードマップ | 認証情報、検証前の機密データ | 公式管理台帳にするか |
| Obsidian | ローカル知識ベース、ADR、プロンプト、アイデアメモ | 開発メモ、設計判断、プロンプト改善案 | 外部共有前提の正式資料のみ | 個人開発メモの置き場にするか |

## 推奨フロー案

1. Codex / Antigravity で実装・検証する。
2. 変更内容を `docs/`、`data/WBS.tsv`、Git commit に反映する。
3. WBS を Google Sheets と Calendar に同期する。
4. 社長説明前に、`docs/` の主要資料を NotebookLM に読み込ませ、想定質問と要約を作る。
5. 進捗・同期結果・レビュー依頼は Slack に短文で流す。
6. 6/2 の議事録と決定事項は Notion DB または Google Docs に集約する。
7. Obsidian には、公開前の設計メモ、ADR、プロンプト検証ログを残す。
8. 公式化した情報だけを `docs/` と WBS に戻し、Git 管理する。

## 6/2 プレゼンで見せる価値

- 社長が資料を読む時間を減らせる。
- 開発中の意思決定が Slack / Notion / WBS に残り、後から追える。
- 個人の思考メモと公式資料の境界を分けられる。
- Gemini quota 制限中でも、Codex、GitHub、Google Workspace、NotebookLM で開発判断を止めにくい。
- 6/2 後にサービス内容が決まったら、選んだ導線だけを正式運用へ昇格できる。

## 6/2 で決める確認事項

- NotebookLM は、社長向け説明資料の要約・QA生成に使うか。
- Slack は、社長向け通知まで含めるか、開発チーム内の通知に限定するか。
- Notion は、議事録と意思決定DBの公式台帳にするか。
- Obsidian は、個人/開発者メモに限定し、公式資料は `docs/` と Notion に戻す運用にするか。
- 4ツールすべてを導入するか、まずは NotebookLM + Notion など最小構成から始めるか。
- 機密情報、個人情報、認証情報の投入禁止ルールをどこまで文書化するか。

## 6/2 までの運用

- 確定機能として実装しない。
- API連携や自動投稿は、社長確認後に正式運用へ昇格する。
- ただし、社長に「実際にやった状態」を見せるため、認証情報や個人情報を含まない範囲で Google Drive / Notion / GitHub Issues への実体連携は証跡として実施する。
- Slack投稿は送信先チャンネルと共有範囲の確認後に行う。
- 手動で見せられる資料導線、画面導線、運用イメージを優先する。
- 追加した WBS タスク `T616` から `T641` は、連携採用判断と実体デモのための準備タスクとして扱う。

## 実装済みデモ成果物

2026-05-21 時点で、社長に「実際にやった状態」を見せるため、外部サービスへ送信しないローカル生成方式で以下を実装した。

生成コマンド:

```powershell
python scripts/generate_knowledge_flow_demo.py
```

ローカル FastAPI 起動中は、画面の「開発ナレッジ連携デモ」からも生成できる。

```text
POST /api/knowledge-flow/generate
GET  /api/knowledge-flow/status
```

生成先:

| 成果物 | パス | 見せ方 |
| --- | --- | --- |
| NotebookLM投入資料 | `exports/knowledge_flow/notebooklm_source_pack.md` / `exports/knowledge_flow/notebooklm_source_pack.txt` | TXT版をGoogle Docsへ変換し、NotebookLM source候補として見せる |
| NotebookLMプレゼンブリーフ | `exports/knowledge_flow/notebooklm_presentation_brief.md` / `exports/knowledge_flow/notebooklm_presentation_brief.txt` | NotebookLMで8枚以内の社長向けプレゼン構成・話す要点・想定QAを作る入力資料として使う |
| Slack投稿案 | `exports/knowledge_flow/slack_ceo_update.md` | 投稿前レビュー用の進捗共有文として見せる |
| Notion意思決定DB | `exports/knowledge_flow/notion_decision_log.csv` | Notion DBへCSV importする候補として見せる |
| Notionバックログ | `exports/knowledge_flow/notion_backlog_import.csv` | WBS連携バックログのimport候補として見せる |
| Obsidian vault | `exports/knowledge_flow/obsidian_vault/` | ローカルvaultとして開ける雛形を見せる |
| デモ手順 | `exports/knowledge_flow/CEO_KNOWLEDGE_FLOW_DEMO_GUIDE.md` | 6/2当日の説明順として使う |
| 連携証跡 | `exports/knowledge_flow/integration_evidence.md` | Drive、Notion、Issues、Project/Slackの到達点を見せる |

この実装では、`client_secret.json`, `credentials.json`, `authorized_user.json` は生成スクリプトから読み込まない。外部連携は、Codexセッションで明示的に実行したDriveアップロード、Notionページ作成、GitHub Issues起票の範囲に限定する。

## 2026-05-21 CLI/MCP 実連携証跡

| 対象 | 実施内容 | URL/結果 |
| --- | --- | --- |
| Google Drive / NotebookLM | `notebooklm_source_pack.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit |
| Google Drive / NotebookLM Presentation | `notebooklm_presentation_brief.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit |
| Notion | 連携証跡ページをNotion MCPで作成 | https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951 |
| GitHub Issues | CEOデモ向け連携タスクを8件起票 | https://github.com/kanta13jp1/mighty-link-ai-connect/issues |
| GitHub Project | `gh project list` と `gh auth refresh` を再試行 | `read:project` / `project` スコープ復旧が必要。Issue #5 / #8、WBS `T633`, `T641`, `T644`, `T645` で管理 |
| Slack | CLI/MCP利用可否を確認 | Slack CLI未検出、送信先チャンネル未確定。Issue #2 / WBS `T636` で管理 |

## 2026-05-22 Workspace OAuth Google Docs 再作成

Google Docsホームで資料が見えない問題に対応するため、Google Drive MCPではなく `authorized_user.json` のLocal OAuth Drive APIを使ってNotebookLM用Google Docsを再作成した。

- 実行アカウント: `k-umezawa@ml-mightylink.com`
- 検証コマンド: `python scripts/verify_google_workspace_account.py`
- 再作成コマンド: `python scripts/upload_notebooklm_docs_to_drive.py`
- Source Pack: https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit
- Presentation Brief: https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit
- メタデータ: `exports/knowledge_flow/google_drive_workspace_docs.json`

以後、NotebookLM投入用のGoogle DocsはMCPコネクタではなく、Workspace OAuth検証済みのLocal Drive APIで作成・更新する。

## 2026-05-22 docs配下のNotebookLM同期導線

AIエージェントがNotebookLMから要約された設計情報・ロードマップ情報を取得して開発判断に使えるよう、`docs/*.md` をWorkspace所有のGoogle Docsへ同期するCLI導線を追加した。

実行コマンド:

```powershell
python scripts/sync_docs_to_notebooklm.py
```

実行結果:

- `docs/*.md` 22件を `k-umezawa@ml-mightylink.com` 所有のGoogle Docsへ同期した。
- 同期manifest: `exports/knowledge_flow/notebooklm_docs_manifest.json`
- NotebookLM CLI再認証手順: `exports/knowledge_flow/notebooklm_cli_next_steps.md`
- Notion証跡ページ: https://www.notion.so/3671d736b9db8164b46dc143befa29eb
- GitHub Issues: [#9](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/9), [#10](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/10)

現状、`notebooklm` CLIはインストール済みだが認証切れのため、NotebookLMへのsource追加と要約取得は `notebooklm login` 後に再実行する。

```powershell
notebooklm login
python scripts/sync_docs_to_notebooklm.py
```

`notebooklm login` では `k-umezawa@ml-mightylink.com` を選択する。再実行後、AIエージェント向けの要約は `exports/knowledge_flow/notebooklm_agent_brief.md` と `.json` に保存される。

## 6/2 後の実装候補

| 候補 | 内容 | 初期実装イメージ |
| --- | --- | --- |
| Slack通知 | WBS同期完了、GitHub Actions結果、デモURL検証結果を通知 | 手動テンプレートから開始し、必要ならWebhook化 |
| Notion DB | 決定事項、保留事項、次アクション、WBS参照IDを管理 | 6/2議事録を元にDB設計 |
| NotebookLM資料パック | README、WBS、判断材料パック、AI pipeline資料を投入 | 社長説明前のQA生成に活用 |
| Obsidian vault | ADR、プロンプト、検証メモをローカルに蓄積 | 公式化する内容だけ `docs/` へ昇格 |

## セキュリティルール

- `client_secret.json`, `credentials.json`, `authorized_user.json` はどの外部ツールにも貼り付けない。
- 個人情報を含む経歴書・案件票は、社長確認前に外部ナレッジツールへ投入しない。
- Slack / Notion に投稿する場合は、要約・タスクID・公開URL・同期結果に絞る。
- Obsidian はローカル保管を前提にし、Git 管理する場合は秘密情報が含まれていないか確認する。

## 2026-05-22 NotebookLM CLI認証完了と要約取得

- NotebookLM CLIは `k-umezawa@ml-mightylink.com` で認証済み。
- NotebookLM notebook: `75521ea6-6b9b-47b2-9508-50050d8ab2d5`
- Notebook title: `Mighty Skill-Bridge Development Knowledge 2026-06-02`
- Source status: `docs/*.md` 22件すべて `ready`
- Agent Brief: `exports/knowledge_flow/notebooklm_agent_brief.md`
- CEO Slide Outline: `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- CLI補助ログイン: `scripts/notebooklm_login_workspace.py`

認証が切れた場合は、通常の `notebooklm login` で遷移中断が起きることがあるため、補助スクリプトを使う。

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py
```

この状態により、AIエージェントはNotebookLMから要約された設計情報・ロードマップ・残課題をローカル成果物として読み込み、次回以降の開発判断に使える。

## 2026-05-22 NotebookLMからPPTXまでの実証

- NotebookLM CLIで取得した `exports/knowledge_flow/notebooklm_ceo_slide_outline.md` を出発点に、社長説明用PowerPoint `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` を生成した。
- 生成スクリプトは `scripts/generate_ceo_presentation_deck.py`。NotebookLM CLIは構成・論点・話すメモの生成、ローカルスクリプトはPPTX組版とパッケージ検証を担当する。
- `@oai/artifact-tool/presentation-jsx` はこのWindowsシェルでは解決できなかったため、今回のPPTX成果物は `python-pptx` で作成した。制約は成果物サマリーと証跡に明記する。
- Google Driveへのアップロード対象にPPTXを追加し、`exports/knowledge_flow/google_drive_workspace_docs.json` の `files.ceo_presentation_pptx` にURLを記録する運用にした。
- Drive URL: `https://docs.google.com/presentation/d/1XGHnQHBpJyyhh_Y3I2lq2UThPRC-2dcL/edit?usp=drivesdk&ouid=117190324786156797159&rtpof=true&sd=true`
- SlackはローカルCLI未検出、送信MCP未露出のため、実送信ではなく投稿案生成と権限確認を継続する。実送信は投稿先チャンネル・共有範囲の承認後に行う。
- GitHub Projectは `read:project` / `project` OAuth scope不足が継続している。Issue #8 / #5で復旧待ちとして扱い、Issueは実装タスク管理、WBSは日程・報告管理として先行運用する。
