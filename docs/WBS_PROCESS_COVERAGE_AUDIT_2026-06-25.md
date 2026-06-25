# WBS 工程網羅性監査（第3回）・サイト開発完了定義追加

作成日: 2026-06-25
担当レーン: VSCode + Codex
関連: [WBS.md](WBS.md) / [PRODUCTION_GO_NO_GO_CHECKLIST.md](PRODUCTION_GO_NO_GO_CHECKLIST.md) / [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md)

---

## 目的

`data/WBS.tsv` の全タスクが完了したときに、そのまま「このサイトの開発完了」と宣言できる状態にするため、企画、設計、実装、テスト、リリース、実運用、保守の工程を再監査した。

今回の監査では、個別機能や個別Runbookの有無だけでなく、最後に全成果物を束ねる完成判定、最新機能を反映したユーザー/管理者ドキュメント、データ保持/削除、外部SaaS/AIモデル棚卸し、会社運用引継ぎがWBS上に明示されているかを確認した。

## 現状サマリ

| 観点 | 既存カバレッジ | 判定 |
| --- | --- | --- |
| 企画 | T101、T611、T804、6/17議事録、営業メールAI最優先化 | 網羅 |
| 設計 | DB/アーキ/セキュリティ、Firebase/Supabase、Stripe、ロールバック、ステージング | 網羅 |
| 実装 | コアAI診断、営業メールAI、従業員アンケート、勤怠、管理者UI、課金、同意UI | 個別タスクは存在 |
| テスト | pytest、public demo guard、アクセシビリティ、外部疑似診断、負荷テスト予定 | 個別タスクは存在 |
| リリース | Go/No-Go、SemVer/GitHub Releases、GAアナウンス、Firebase/GitHub Pages | 個別タスクは存在 |
| 実運用 | 監視、サポート、月次品質レポート、DR、インシデント、コスト、OAuth復旧 | 個別タスクは存在 |
| 保守 | 依存更新、Supabase PG upgrade、モデル追従、ログ退避、年次規約見直し | 個別タスクは存在 |
| 完成判定 | 全WBS完了時の最終横断ゲート、最新docs、全テーブル保持/削除、外部SaaS棚卸し、会社運用引継ぎ | 不足 |

## 追加した不足タスク

| ID | タスク | 目的 |
| --- | --- | --- |
| T844 | WBS工程網羅性監査（第3回）・サイト開発完了定義と不足タスク追加 | 本監査そのもの。今回完了扱い |
| T845 | 全機能本番受入E2E/UAT最終再検証 | 新規追加機能を含む全ユーザー/管理者導線を本番相当で再確認する |
| T846 | ユーザー操作ガイド・管理者Runbook・FAQの全機能最終更新 | T744の古い操作ガイドを、営業メールAI、従業員アンケート、勤怠、管理者UI、課金、削除/エクスポートへ追従させる |
| T847 | 本番データ保持・削除・匿名化ポリシーの全テーブル実装照合 | T840/T841/T817系で増えた新テーブルを含め、保持・削除・匿名化・RLS・原本非保存を横断確認する |
| T848 | AIモデル・外部SaaS・連携サービス棚卸しとGA時点利用可否の最終凍結 | 公式Docs確認対象の各サービスについて、実採用/非採用、モデル名、API version、契約、fallback、secret管理を凍結する |
| T849 | サイト開発完了総合判定・WBS全完了証跡化・GAリリース閉鎖 | 全WBS完了、Go/No-Go、GitHub、Sheets/Calendar、main/master、GA tag、Firebase、NotebookLM/Drive一致を確認し、開発完了を宣言する |
| T850 | 会社運用引継ぎリハーサル・権限棚卸し・Break-glass確認 | T823移管後に、会社側が復旧、問い合わせ、権限変更、緊急対応を実行できることを確認する |

## Release Gate への反映

`data/release_go_no_go_criteria.tsv` に `PUBLIC-13` を追加した。

`PUBLIC-13` は、T845からT850までの横断ゲートが完了するまで `public_paid_launch` と「サイト開発完了宣言」を止めるための判定項目である。

## 課題・QAへの反映

- R99: WBS全完了をサイト開発完了とみなすための最終横断ゲート不足
- QA-76: WBSの全タスクが完了したら、このサイトの開発は完了と言えるか

## 完了定義

T849を完了できる条件は次の通り。

1. `data/WBS.tsv` の全タスクが `完了`。
2. `data/release_go_no_go_criteria.tsv` の `public_paid_launch` 必須項目が `PASS` または人間承認済み。
3. GitHub Issues / Project #1 に未完了の開発必須Issueが残っていない。
4. Google Sheets、Google Calendar、NotebookLM/Driveが最新のWBS/docsと同期済み。
5. `main`、`master`、GA tag、GitHub Release、Firebase Hosting/Functions、公開デモURLの内容が一致している。
6. 会社アカウント移管、請求、権限、Break-glass、secret管理が会社運用へ引き継がれている。
7. secret、OAuth token、実メール本文、CSV原本、個人データ実値、契約金額実値をGitHub、Sheets、docs、NotebookLM、Issueへ記録していない。

## 公式ドキュメント確認メモ

今回の判断では、次の公式ドキュメントを確認した。

- Claude Code overview / memory / settings / security
- OpenAI Codex overview / AGENTS.md / best practices / MCP
- Gemini models / context caching、Google Sheets batchUpdate、Gmail API
- Firebase Hosting / Functions
- Supabase getting started / Row Level Security
- GitHub Actions / Issues / Projects / Pages
- Stripe Billing / Customer Portal / Tax
- Notion、Slack、Figma、Canva、Discord、Firecrawl、InsForge、DeepSeek、xAI、Kimi、Microsoft Foundry、Amazon Bedrock、Apple HIG、Unity、Obsidian、お名前.com など、`MULTI_AI_WORKFLOW.md` のセッションゲート対象

長い引用は残さず、WBSへ効く差分だけを反映した。DeepSeekは `deepseek-chat` / `deepseek-reasoner` の廃止予定が示されていたため、T848の棚卸しで外部AIモデル名と廃止予定を最終確認する。
