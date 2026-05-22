# 6/2 社長デモ向け 連携実施証跡

作成日: 2026-05-21
更新日: 2026-05-22

## 目的

6/2 の社長打ち合わせで「実際にやった状態」を見せるため、NotebookLM、Slack、Notion、Obsidian、GitHub Issues、GitHub Project の連携状況を証跡として残す。

実際の企画・サービス内容は 6/2 に決定するため、本資料では開発フローとタスク管理の実装・確認結果だけを扱う。

## 実施済み

| 項目 | 実施内容 | 証跡 |
| --- | --- | --- |
| GitHub Issues | CEOデモ向け連携タスクを13件起票 | [#1](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/1), [#2](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/2), [#3](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/3), [#4](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/4), [#5](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/5), [#6](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/6), [#7](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/7), [#8](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/8), [#9](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/9), [#10](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/10), [#11](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/11), [#13](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/13) |
| NotebookLM / Google Drive | `notebooklm_source_pack.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit |
| NotebookLM / プレゼン作成 | `notebooklm_presentation_brief.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit |
| Notion | Notion MCPで連携証跡ページを作成 | https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951 |
| Obsidian | `exports/knowledge_flow/obsidian_vault/` にvault雛形と `.obsidian` 設定を追加 | `exports/knowledge_flow/obsidian_vault/Mighty Skill-Bridge Home.md` |
| Slack | 投稿案を生成し、CLI/MCP利用可否を確認 | `exports/knowledge_flow/slack_ceo_update.md` |
| Google Workspace OAuth | `authorized_user.json` の実行アカウントをDrive APIで検証 | `k-umezawa@ml-mightylink.com` |
| NotebookLM docs同期 | `docs/*.md` 22件をWorkspace Google Docsへ同期 | `exports/knowledge_flow/notebooklm_docs_manifest.json` |
| NotebookLM CLI | ローカルCLI認証とsource状態確認 | notebook `75521ea6-6b9b-47b2-9508-50050d8ab2d5`、22 sources ready |
| Notion証跡更新 | NotebookLM docs同期の子ページを作成 | https://www.notion.so/3671d736b9db8164b46dc143befa29eb |

## CLI / MCP 実行結果

| 操作 | コマンド/ツール | 結果 |
| --- | --- | --- |
| GitHub Issue起票 | `gh issue create` | Issue #1〜#11 と #13 を作成 (#12 はPR番号) |
| NotebookLMプレゼン導線 | `python scripts/upload_notebooklm_docs_to_drive.py` | Presentation Brief を `k-umezawa@ml-mightylink.com` 所有のGoogle Docsへ変換し直した |
| GitHub Project確認 | `gh project list --owner kanta13jp1 --format json` | `read:project` スコープ不足で停止 |
| GitHub Project認証再試行 | `gh auth refresh -h github.com -s read:project -s project` | 2分でタイムアウト。Issue #8として手動認証待ちに分離 |
| Google Drive連携 | `python scripts/upload_notebooklm_docs_to_drive.py` | TXT source pack を `authorized_user.json` 経由でGoogle Docsへ変換し、ownerが `k-umezawa@ml-mightylink.com` であることを確認 |
| Notion連携 | Notion MCP `_notion_create_pages` | GitHub配下のNotionページとして証跡を作成 |
| Slack CLI確認 | `Get-Command slack` | ローカルCLIは未検出 |
| Google Workspaceアカウント確認 | `python scripts/verify_google_workspace_account.py` | `authorized_user.json` が `k-umezawa@ml-mightylink.com` に紐づいていることを確認 |
| NotebookLM docs同期 | `python scripts/sync_docs_to_notebooklm.py` | Google Docs同期、NotebookLM source追加、Agent Brief、CEO Slide Outline生成が完了 |
| GitHub Issues追加 | `gh issue create` / `gh issue comment` | Issue #9 / #10 / #11 / #13を追加し、Issue #8へProject権限不足の最新状況を追記 |
| GitHub Issues完了反映 | `gh issue close` | Issue #7 / #9 / #10 / #11 / #13 を成果物リンク付きでクローズ |

## 2026-05-22 Google Docsアカウント修正

Google DocsホームでNotebookLM用資料が表示されない問題があったため、Codex/Google Drive MCPで作成した旧Docsではなく、ローカルOAuth `authorized_user.json` を使うDrive APIアップロードへ切り替えた。

- Source Pack: https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit
- Presentation Brief: https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit
- owner: `k-umezawa@ml-mightylink.com`
- 証跡JSON: `exports/knowledge_flow/google_drive_workspace_docs.json`

## 2026-05-22 docs配下のNotebookLM同期

`scripts/sync_docs_to_notebooklm.py` を追加し、`docs/*.md` 22件をWorkspace所有のGoogle Docsへ同期した。NotebookLM CLIは補助ログイン導線で再認証し、source追加と要約取得まで完了した。

- Manifest: `exports/knowledge_flow/notebooklm_docs_manifest.json`
- Next steps: `exports/knowledge_flow/notebooklm_cli_next_steps.md`
- 再ログイン補助コマンド: `python scripts/notebooklm_login_workspace.py` → `python scripts/sync_docs_to_notebooklm.py`
- NotebookLM notebook: `75521ea6-6b9b-47b2-9508-50050d8ab2d5`
- Agent Brief: `exports/knowledge_flow/notebooklm_agent_brief.md`
- CEO Slide Outline: `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- GitHub Issue #9: https://github.com/kanta13jp1/mighty-link-ai-connect/issues/9
- GitHub Issue #10: https://github.com/kanta13jp1/mighty-link-ai-connect/issues/10
- Notion子ページ: https://www.notion.so/3671d736b9db8164b46dc143befa29eb

## GitHub Project の現状

GitHub Project は、現在の `gh` 認証トークンに `read:project` スコープが不足しているため、CLIからProject一覧取得・カード配置ができない。

復旧手順:

```powershell
gh auth refresh -s read:project
gh project list --owner kanta13jp1 --format json
```

復旧後は Issue #1〜#11 と #13 を CEO Demo 用Projectへ配置する。正式対応は WBS `T641`, `T644`, `T645`, `T652` と GitHub Issue #5 / #8 で管理する。

## Slack の現状

このCodexセッションではSlack送信用MCPツールが露出しておらず、ローカルのSlack CLIも検出されなかった。

6/2までの扱い:

- 投稿案は `exports/knowledge_flow/slack_ceo_update.md` に生成済み。
- 投稿先チャンネル、共有範囲、社長宛の通知有無は 6/2 の確認事項にする。
- 正式連携は、Slack connector またはWebhookの権限が整ってから WBSへ昇格する。

## WBS 反映

本作業は `data/WBS.tsv` に `T632` から `T666` として追加・更新した。

- `T632`: GitHub Issues連携
- `T633`: GitHub Project連携
- `T634`: NotebookLM実連携
- `T635`: Notion実連携
- `T636`: Slack連携確認
- `T637`: Obsidian実連携
- `T638`: 連携証跡台帳
- `T639`: Issue-WBS運用
- `T640`: 連携デモリハーサル
- `T641`: Project正式ボード化
- `T642`: NotebookLMプレゼン資料化
- `T643`: NotebookLMスライド草案
- `T644`: Project OAuth復旧
- `T645`: Project Issue配置
- `T646`: Slack送信権限確認
- `T647`: Google Workspaceアカウント固定
- `T648`: Workspace Google Docs再作成
- `T649`: docs NotebookLM同期
- `T650`: NotebookLM CLI認証復旧
- `T651`: NotebookLM Agent Brief取得
- `T656`: NotebookLM補助ログイン導線
- `T657`: NotebookLM社長スライド草案取得
- `T652`: GitHub Project再確認
- `T653`: Slack連携実送信準備
- `T654`: Notion証跡更新
- `T655`: Obsidian Agent Brief導線
- `T664`: 三ツール開発フロー整備
- `T665`: 古いドキュメント削除・最新化
- `T666`: Calendar完了イベント削除

同期結果:

- Google Sheets: `82 source rows` / `94 hierarchical WBS display rows` (81 task rows + header)
- Google Sheets tracker tabs: `課題管理表` 28 rows / `QA表` 36 rows
- Google Calendar: 初回 cleanup で `Deleted completed: 17`、直近再同期は `Active: 13, Success: 13, Updated: 13, Failed: 0, Deleted completed: 0, Deleted stale: 0`
- Calendar反映イベント例: `GitHub Project権限復旧チェック`, `Slack投稿先・送信権限確認`, `GitHub Issues/Project再追跡`, `6/2資料最終パックレビュー`, `社長プレゼン最終リハーサル`, `第1回 社長報告会`

## 社長への見せ方

1. 公開デモURLを開く。
2. 「開発ナレッジ連携デモ」セクションを見せる。
3. NotebookLMの `Agent Brief` と `CEO Slide Outline` を開き、AIが資料を要約して開発・プレゼンに使う流れを見せる。
4. Google Docs化したNotebookLM source packを開く。
5. Notion証跡ページを開く。
6. GitHub Issues #1-#11/#13/#14/#16 とGoogle Sheets `課題管理表` / `QA表` を見せ、Projectは権限復旧待ちとして説明する。
7. Obsidian vaultの `Mighty Skill-Bridge Home.md` を開く。
8. Slack投稿案を見せ、チャンネルと共有範囲の判断を依頼する。

## 2026-05-22 追加証跡: NotebookLM PowerPoint化

| 項目 | 実施内容 | 証跡 |
| --- | --- | --- |
| NotebookLM CLI | 22 source readyのNotebookからCEO Slide Outlineを取得済み | `exports/knowledge_flow/notebooklm_ceo_slide_outline.md` |
| PowerPoint生成 | NotebookLM由来の8枚構成を社長説明用PPTXに変換 | `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` |
| 生成スクリプト | PPTXを再生成できるスクリプトを追加 | `scripts/generate_ceo_presentation_deck.py` |
| Drive共有 | PPTXをWorkspace OAuthでGoogle Driveへアップロードする処理を追加 | https://docs.google.com/presentation/d/1XGHnQHBpJyyhh_Y3I2lq2UThPRC-2dcL/edit?usp=drivesdk&ouid=117190324786156797159&rtpof=true&sd=true |
| Notion証跡 | PPTX生成・Drive共有・Slack/Project制約をNotion MCPで記録 | https://www.notion.so/3671d736b9db81d3ac3cc7a716699c37 |

追加WBS:

- `T658`: NotebookLM PowerPoint化
- `T659`: PowerPoint Drive共有
- `T660`: Notion PPTX証跡更新
- `T661`: GitHub Issues/Project再追跡
- `T662`: Slack MCP/CLI到達性証跡
- `T663`: 6/2資料最終パックレビュー
- `T664`: 三ツール開発フロー整備
- `T665`: 古いドキュメント削除・最新化
- `T666`: Calendar完了イベント削除

今回のCalendar運用変更:

- 完了済みWBSに対応する `NotebookLM PowerPoint化` / `PowerPoint Drive共有・Notion証跡更新` / `三ツール開発フロー整備` などはCalendarから削除
- `GitHub Issues/Project再追跡` / `6/2資料最終パックレビュー` / `社長プレゼン最終リハーサル` / `第1回 社長報告会` は未完了・会議イベントとして維持

## 2026-05-22 追加証跡: 三ツール開発フロー + Sheets tracker同期

| 項目 | 実施内容 | 証跡 |
| --- | --- | --- |
| Codex共通指示 | repo rootに `AGENTS.md` を追加 | `AGENTS.md` |
| Claude Code memory | `CLAUDE.md` から `@AGENTS.md` をimport | `CLAUDE.md` |
| Sheets tracker同期 | `sync_wbs_to_sheets.py` に `課題管理表` / `QA表` 同期を統合 | `scripts/sync_wbs_to_sheets.py` |
| 課題管理表 | HANDOFF-2/10/11をresolved化しIssue #13を関連付け | `data/issues_tracker.tsv` |
| QA表 | 公式Docs毎回確認ルールを `Q-AHOC-20260522-1` として追加 | `data/qa_tracker.tsv` |
| GitHub Issue | T664証跡Issueを作成してクローズ | https://github.com/kanta13jp1/mighty-link-ai-connect/issues/13 |
| Actions警告 | Pages deployは成功したがNode.js 20 deprecation annotationを検出し、課題管理表へ反映 | https://github.com/kanta13jp1/mighty-link-ai-connect/issues/14 |
