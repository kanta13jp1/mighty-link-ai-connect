# WBS 再レビュー 2026-06-26

作成日: 2026-06-26
担当レーン: Codex
関連WBS: T844, T845, T846, T847, T848, T849, T850, T851, T852
関連Issue: #131, #132, #133, #134, #135, #136, #137, #138, #139

---

## 結論

2026-06-25のT844で追加したT845からT850までの横断ゲートにより、WBS全タスク完了時にサイト開発完了を宣言できる構造は維持されている。

ただし、今回の再レビュー後にmain CIを確認したところ、Firebase deployでWorkload Identity Federation経由のApplication Default CredentialsがFirebase CLIに認識されず、legacy `FIREBASE_TOKEN` も再認証期限切れで失敗することを確認した。これは、アプリ変更時の本番反映、緊急修正、GA判定に影響するため、WBSから漏れていた本番リリース前タスクとして追加する。

したがって、今回追加する作業タスクは、レビュー記録であるT851と、Firebase CI/CD本番デプロイ認証を再構成するT852とする。T851は本ファイル作成と同期確認をもって完了、T852は未着手の公開前必須ゲートとして追跡する。

## 確認した完了ゲート

| WBS | 状態 | 役割 |
| --- | --- | --- |
| T844 | 完了 | WBS工程網羅性監査（第3回）と不足タスク追加 |
| T845 | 未着手 | 全機能本番受入E2E/UAT最終再検証 |
| T846 | 未着手 | ユーザー操作ガイド、管理者Runbook、FAQの全機能最終更新 |
| T847 | 未着手 | 本番データ保持、削除、匿名化ポリシーの全テーブル実装照合 |
| T848 | 未着手 | AIモデル、外部SaaS、連携サービス棚卸しとGA時点利用可否の最終凍結 |
| T849 | 未着手 | サイト開発完了総合判定、WBS全完了証跡化、GAリリース閉鎖 |
| T850 | 未着手 | 会社運用引継ぎリハーサル、権限棚卸し、Break-glass確認 |
| T851 | 完了 | 本再レビューとFirebase CI認証ゲート追加判定 |
| T852 | 未着手 | Firebase CI/CD本番デプロイ認証（WIF/ADC）再構成とFIREBASE_TOKEN廃止 |

## 完了定義

サイト開発完了の最終宣言はT849で行う。

T849を完了できる条件は次の通り。

1. `data/WBS.tsv` の全タスクが完了している。
2. `data/release_go_no_go_criteria.tsv` の公開前必須ゲートが `PASS` または承認済みである。
3. GitHub Issues / Project #1 に未完了の開発必須Issueが残っていない。
4. Google Sheets、Google Calendar、Drive/NotebookLM向けdocsが最新のWBS/docsと同期済みである。
5. `main`、`master`、GA tag、GitHub Release、Firebase Hosting/Functions、公開デモURLの内容が一致している。
6. 会社アカウント移管、請求、権限、Break-glass、secret管理が会社運用へ引き継がれている。
7. secret、OAuth token、実メール本文、CSV原本、個人データ実値、契約金額実値がGitHub、Sheets、docs、NotebookLM、Issueへ記録されていない。
8. GitHub ActionsからFirebase Hosting/Functionsへ、会社管理のWIF/service account/secret経路で本番deployできることが、アプリ変更を含むmain CIで確認されている。

## 追加した抜けタスク

| WBS | 追加理由 | 完了条件 |
| --- | --- | --- |
| T852 | main CIのFirebase deploy認証がWIF/ADCおよびlegacy `FIREBASE_TOKEN` の両方で失敗し、アプリ変更時の本番反映経路が未確定だったため | GCP project_id、WIF provider、service account権限、Firebase deploy権限、Functions runtime env secretを会社管理の正規経路へ再構成し、アプリ変更時のmain deploy greenを証跡化する |

T852に対応して、`data/release_go_no_go_criteria.tsv` へPUBLIC-14、`data/issues_tracker.tsv` へR100、`data/qa_tracker.tsv` へQA-77を追加した。docs/data/exportsのみの変更ではFirebase deployをskipする暫定ガードを入れたが、これは本番デプロイ成功の代替証跡ではない。

## 公式ドキュメント確認メモ

今回の再レビューでは、WBS、AI駆動開発、同期、公開デモ、外部連携の判断に関係する公式ドキュメントを確認した。

- Claude Code overview / memory / settings / security
- OpenAI Codex overview / AGENTS.md / best practices / MCP
- Gemini models / context caching、Google Sheets batchUpdate、Google Calendar API
- Firebase Hosting / Functions
- Supabase getting started / Row Level Security
- GitHub Actions / Projects / Pages
- GitHub Actions OIDC for Google Cloud、Firebase CLI、Firebase Hosting GitHub integration
- Stripe Billing、Slack、Notion、Figma、Canva、Discord、Firecrawl、InsForge、Reddit、WordPress REST API、お名前.comなど

長い引用は残さず、WBSへ効く差分だけを反映した。今回の確認では、T845からT850の完了ゲートに加えて、CI/CD本番デプロイ認証をT852として明示する必要があると判断した。
