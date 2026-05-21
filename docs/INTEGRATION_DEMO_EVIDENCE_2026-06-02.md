# 6/2 社長デモ向け 連携実施証跡

作成日: 2026-05-21
更新日: 2026-05-22

## 目的

6/2 の社長打ち合わせで「実際にやった状態」を見せるため、NotebookLM、Slack、Notion、Obsidian、GitHub Issues、GitHub Project の連携状況を証跡として残す。

実際の企画・サービス内容は 6/2 に決定するため、本資料では開発フローとタスク管理の実装・確認結果だけを扱う。

## 実施済み

| 項目 | 実施内容 | 証跡 |
| --- | --- | --- |
| GitHub Issues | CEOデモ向け連携タスクを8件起票 | [#1](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/1), [#2](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/2), [#3](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/3), [#4](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/4), [#5](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/5), [#6](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/6), [#7](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/7), [#8](https://github.com/kanta13jp1/mighty-link-ai-connect/issues/8) |
| NotebookLM / Google Drive | `notebooklm_source_pack.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit |
| NotebookLM / プレゼン作成 | `notebooklm_presentation_brief.txt` をLocal OAuth Drive APIでGoogle Docsへ変換 | https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit |
| Notion | Notion MCPで連携証跡ページを作成 | https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951 |
| Obsidian | `exports/knowledge_flow/obsidian_vault/` にvault雛形と `.obsidian` 設定を追加 | `exports/knowledge_flow/obsidian_vault/Mighty Skill-Bridge Home.md` |
| Slack | 投稿案を生成し、CLI/MCP利用可否を確認 | `exports/knowledge_flow/slack_ceo_update.md` |
| Google Workspace OAuth | `authorized_user.json` の実行アカウントをDrive APIで検証 | `k-umezawa@ml-mightylink.com` |

## CLI / MCP 実行結果

| 操作 | コマンド/ツール | 結果 |
| --- | --- | --- |
| GitHub Issue起票 | `gh issue create` | Issue #1 から #8 を作成 |
| NotebookLMプレゼン導線 | `python scripts/upload_notebooklm_docs_to_drive.py` | Presentation Brief を `k-umezawa@ml-mightylink.com` 所有のGoogle Docsへ変換し直した |
| GitHub Project確認 | `gh project list --owner kanta13jp1 --format json` | `read:project` スコープ不足で停止 |
| GitHub Project認証再試行 | `gh auth refresh -h github.com -s read:project -s project` | 2分でタイムアウト。Issue #8として手動認証待ちに分離 |
| Google Drive連携 | `python scripts/upload_notebooklm_docs_to_drive.py` | TXT source pack を `authorized_user.json` 経由でGoogle Docsへ変換し、ownerが `k-umezawa@ml-mightylink.com` であることを確認 |
| Notion連携 | Notion MCP `_notion_create_pages` | GitHub配下のNotionページとして証跡を作成 |
| Slack CLI確認 | `Get-Command slack` | ローカルCLIは未検出 |
| Google Workspaceアカウント確認 | `python scripts/verify_google_workspace_account.py` | `authorized_user.json` が `k-umezawa@ml-mightylink.com` に紐づいていることを確認 |

## 2026-05-22 Google Docsアカウント修正

Google DocsホームでNotebookLM用資料が表示されない問題があったため、Codex/Google Drive MCPで作成した旧Docsではなく、ローカルOAuth `authorized_user.json` を使うDrive APIアップロードへ切り替えた。

- Source Pack: https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit
- Presentation Brief: https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit
- owner: `k-umezawa@ml-mightylink.com`
- 証跡JSON: `exports/knowledge_flow/google_drive_workspace_docs.json`

## GitHub Project の現状

GitHub Project は、現在の `gh` 認証トークンに `read:project` スコープが不足しているため、CLIからProject一覧取得・カード配置ができない。

復旧手順:

```powershell
gh auth refresh -s read:project
gh project list --owner kanta13jp1 --format json
```

復旧後は Issue #1 から #8 を CEO Demo 用Projectへ配置する。正式対応は WBS `T641`, `T644`, `T645` と GitHub Issue #5 / #8 で管理する。

## Slack の現状

このCodexセッションではSlack送信用MCPツールが露出しておらず、ローカルのSlack CLIも検出されなかった。

6/2までの扱い:

- 投稿案は `exports/knowledge_flow/slack_ceo_update.md` に生成済み。
- 投稿先チャンネル、共有範囲、社長宛の通知有無は 6/2 の確認事項にする。
- 正式連携は、Slack connector またはWebhookの権限が整ってから WBSへ昇格する。

## WBS 反映

本作業は `data/WBS.tsv` に `T632` から `T641` として追加した。

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

同期結果:

- Google Sheets: `63 source rows` / `75 hierarchical WBS display rows`
- Google Calendar: `Success: 18, Updated: 17, Failed: 0`
- 新規Calendarイベント: `CLI/MCP連携証跡レビュー`, `GitHub Project権限復旧チェック`, `NotebookLMプレゼン草案作成`, `Slack投稿先・送信権限確認`, `Google Workspace OAuthアカウント固定確認`

## 社長への見せ方

1. 公開デモURLを開く。
2. 「開発ナレッジ連携デモ」セクションを見せる。
3. Google Docs化したNotebookLM source packを開く。
4. Notion証跡ページを開く。
5. GitHub Issues #1-#6 を見せ、Projectは権限復旧待ちとして説明する。
6. Obsidian vaultの `Mighty Skill-Bridge Home.md` を開く。
7. Slack投稿案を見せ、チャンネルと共有範囲の判断を依頼する。
