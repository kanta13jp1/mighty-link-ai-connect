# AIモデル・外部SaaS・連携サービス GA凍結Runbook

- 作成日: 2026-06-27
- 対象: Mighty-Link AI Connect / Mighty Skill-Bridge
- 関連WBS: T827, T844, T846, T847, T848, T849, T850, T852, T854
- 関連Issue: #135
- 判定: T848完了。`public_paid_launch` は残ゲート完了までNo-Go

---

## 目的

公式ドキュメント確認対象のAIモデル、外部SaaS、連携サービスについて、GA時点での採用/非採用、モデル名、API version、fallback、secret管理、会社請求移管状態を凍結する。

このRunbookは、WBS全完了をサイト開発完了とみなすための外部連携正本である。ここにない外部API、モデル、SaaSをGA前に追加する場合は、WBS、課題管理表、QA表、Go/No-Go、secret管理、請求移管を更新してから採用する。

## GA凍結サマリー

| 区分 | GA時点の扱い | 対象 |
| --- | --- | --- |
| 本番ランタイム採用 | 採用。ただし残ゲート完了まで有償一般公開はしない | Firebase Hosting/Functions/GCP、Supabase、Google Workspace、GitHub、Stripe、Gemini API |
| 開発・運用レーン採用 | 採用。成果物と意思決定はWBS/docs/GitHub/Sheetsへ残す | Antigravity + Gemini、VSCode + Codex、VSCode + Claude Code、NotebookLM、Obsidian |
| 条件付き採用 | 設計・資料・通知の補助として採用。secret未設定時はskip/dry-run | Slack、Notion、Figma、Canva |
| レジストラ採用 | ドメイン管理として採用。API自動化はGA時点では非採用 | お名前.com |
| 非採用・保留 | GAランタイムへ組み込まない。将来採用時は別WBSで再審査 | Anthropic API、OpenAI API、Microsoft Azure AI Foundry、Meta Llama、Amazon Bedrock、Apple ML、xAI/Grok、Kimi、MiMo、DeepSeek、BytePlus/Seedance、Reddit、InsForge、FireCrawl、Discord、Unity |

## 本番ランタイム・運用採用サービス

| サービス | GA採用判定 | モデル/API/Version | secret管理 | 会社請求・所有者 | fallback / 未完了ゲート |
| --- | --- | --- | --- | --- | --- |
| Firebase Hosting / Functions / GCP | 採用 | Firebase Hosting、Functions、GCP IAM/Cloud Logging | `FIREBASE_*`、service account、WIF設定はGitHub Secrets/GCP IAMのみ。実値は記録しない | T823/T850で会社管理へ移管 | T852でWIF/ADC正規化とアプリ変更時main deploy greenが必要 |
| Supabase | 採用 | Postgres、RLS、Supavisor pooler、migration | `SUPABASE_DB_URL`、service role、anon keyは環境変数/GitHub Secretsのみ | T823/T850で会社Organizationへ移管 | RLS/REVOKEはT847で照合済み。T845でE2E再確認 |
| Google Workspace / Sheets / Calendar / Drive / NotebookLM | 採用 | Sheets API batchUpdate、Calendar API、Drive/Docs同期、NotebookLM source同期 | OAuth filesとtokenはGit対象外。`k-umezawa@ml-mightylink.com` を検証 | 会社提供Googleアカウントを使用中 | sync失敗時はOAuth再認証Runbookに従う |
| GitHub / Actions / Issues / Project / Pages | 採用 | GitHub Actions、Issues、Project #1、Pages mirror | GitHub Secrets/Varsのみ。secret実値はIssue/Sheets/docsへ記録しない | T823/T850で会社Organization/権限へ移管 | main/master同期とActions greenを毎回確認 |
| Stripe | 条件付き採用 | Customer Portal session API、Billing/WebhookはT807/T791側で残確認 | `STRIPE_SECRET_KEY`、webhook secretはSecretsのみ | 会社Stripeアカウント・会社請求へ移管 | live課金はT807/T791/法務ゲート完了までNo-Go |
| Gemini API | 採用 | 現行コードは `gemini-2.5-flash` を営業メール抽出/NotebookLM補助の既定候補として固定。公式Docs上の最新安定版候補はT769/T780で移行検証する | `GEMINI_API_KEY` は環境変数/GitHub Secretsのみ | T823/T850で会社契約/請求へ移管 | key未設定時はdeterministic fallback。モデル変更は別WBS |
| Antigravity + Gemini | 採用 | フロントエンドpolish、ブラウザエージェント確認、視覚デモ | IDE/CLI認証情報はローカル/会社管理のみ | T850で運用引継ぎ | 実装正本はGitとWBSに残す |
| VSCode + Codex | 採用 | バックエンド、同期、GitHub CLI、Google Workspace自動化、CI/guard | Codex設定とtokenはローカル/管理対象。実値非記録 | T850で運用引継ぎ | AGENTS.mdとCodex manualに従う |
| VSCode + Claude Code | 採用 | docs、review、triage、checklist、第三者レビュー | Claude Code設定はローカル/管理対象。実値非記録 | T850で運用引継ぎ | docs正本とWBS更新を必須にする |

## 条件付き・非採用サービス

| サービス | GA凍結判定 | 理由・条件 | 将来採用時の再審査 |
| --- | --- | --- | --- |
| Anthropic API | 非採用 | Claude Codeは開発レーンとして使うが、アプリ本番APIには組み込まない | モデル名、データ保持、DPA、費用、fallbackを別WBS化 |
| OpenAI API | 非採用 | Codexは開発レーンとして使うが、アプリ本番APIには組み込まない | Responses/Agents等を使う場合はモデル・tool・監査設計を追加 |
| Microsoft Azure AI Foundry | 非採用 | 会社Azure契約、容量、RBAC未凍結 | Azure採用時は容量、リージョン、RAI policy、請求をT823/T850へ接続 |
| Meta Llama | 非採用 | 現行アプリにLlama推論基盤なし | self-host/managed採用時はライセンス、GPU、監査、fallbackを追加 |
| Amazon Bedrock | 非採用 | AWSアカウント/Bedrock運用は現行GA範囲外 | 採用時はIAM、リージョン、モデル、ログ、請求を追加 |
| Apple ML / HIG | 非採用 | iOS/macOSネイティブML実装なし。UI原則の参考のみ | ネイティブアプリ化時にHIG/ML配布を再審査 |
| xAI / Grok | 非採用 | 本番API key、契約、利用目的が未確定 | 採用時はモデル名、データ利用条件、fallbackを追加 |
| Kimi / Moonshot AI | 非採用 | 本番利用なし | 採用時はAPI version、モデル名、データ保持、請求を追加 |
| MiMo | 非採用 | 調査対象。現行GAには組み込まない | 研究利用する場合はライセンスと推論環境を確認 |
| DeepSeek | 非採用 | 現行GAには組み込まない。旧名 `deepseek-chat` / `deepseek-reasoner` は2026-07-24 15:59 UTC廃止予定 | 採用する場合は `deepseek-v4-flash` / `deepseek-v4-pro` を前提に再審査 |
| BytePlus / Seedance | 非採用 | 動画/視覚デモ用途の調査対象。本番アプリAPIでは使わない | 採用時は地域、データ保持、生成物権利、請求を確認 |
| Slack | 条件付き採用 | 月次品質レポート通知payloadはあるが、secret未設定時はskip | 本送信前にWorkspace、Webhook、投稿先、権限、監査を確認 |
| Notion | 条件付き採用 | 月次品質レポート投稿payloadはあるが、secret未設定時はskip | 本送信前にparent/database、token、共有範囲、監査を確認 |
| Obsidian | 採用 | ローカル/Drive向け知識ベース生成のみ。外部APIなし | 共有vault化する場合は権限と個人情報混入を確認 |
| Unity | 非採用 | 3D/ゲーム実装なし | 3Dデモ化時のみ別WBS |
| Figma | 条件付き採用 | 資料/デザイン確認レーン。アプリ本番依存なし | API/MCP自動化時はtoken管理と共有範囲を確認 |
| Canva | 条件付き採用 | CEO資料作成レーン。アプリ本番依存なし | API/MCP自動化時はアプリ権限、公開範囲、請求を確認 |
| Reddit | 非採用 | 本番データ取得、投稿、分析は行わない | 採用時はAPI規約、個人情報、レート制限、OAuthを確認 |
| InsForge | 非採用 | 現行バックエンドはFirebase、DBはSupabaseで凍結 | 採用時はFirebase/Supabaseからの移行計画を別WBS化 |
| FireCrawl | 非採用 | 本番クローリング機能なし | 採用時はrobots、著作権、PII、API key管理を確認 |
| Discord | 非採用 | 本番通知・bot運用なし | 採用時はBot token、投稿先、監査ログ、権限を確認 |
| お名前.com | レジストラ採用 | `mightylink-app.com` のレジストラ。DNS/WordPress/FTP情報の実値は記録しない | API自動化は非採用。DNS変更は人間確認とバックアップ必須 |

## 凍結ルール

1. GA前に新しい外部AIモデルやSaaSを本番導線へ追加しない。
2. モデル名は曖昧な別名ではなく、公式Docsで確認したIDをWBSへ記録する。
3. secret、OAuth token、API key、service account JSON、DB URL、Webhook URL、FTP/WordPress認証情報は、GitHub、Sheets、Issue、docs、NotebookLM、Slack、Notionへ記録しない。
4. secret未設定時はfail closed、dry-run、またはdeterministic fallbackにする。勝手に個人アカウントのkeyへfallbackしない。
5. 会社請求/会社所有へ移管できないサービスは、public_paid_launch前に非採用または人間承認済み非ブロッカーへ分類する。
6. DeepSeekを将来採用する場合、廃止予定の `deepseek-chat` / `deepseek-reasoner` は使わず、現行モデルIDで再設計する。
7. Firebase/GCP、Supabase、Stripe、Google Workspace、GitHubはT823/T850で会社運用引継ぎを完了するまで属人化リスクを残す。
8. Geminiの新しい安定版/previewへ移行する場合、既存の `gemini-2.5-flash` を黙って差し替えず、T769/T780で抽出精度、費用、rate limit、fallback、prompt差分を検証してから変更する。

## T849への申し送り

- T848は外部連携棚卸しとGA凍結の文書/静的照合ゲートであり、一般公開・有償ローンチの許可ではない。
- T849では、本Runbookの「本番ランタイム採用」以外の外部APIが本番コード、CI/CD、GitHub Secrets、Google Sheets、Calendar、NotebookLM、Issueに追加されていないことを再確認する。
- T850では、採用サービスの管理者、請求先、退職時権限削除、Break-glass、secret再発行手順を会社運用としてリハーサルする。

## 公式ドキュメント確認メモ

今回のT848では、次の公式/一次情報を確認した。長い引用は残さず、WBSへ効く採用判断だけを本Runbookへ反映した。

- Anthropic Claude Code / Anthropic Docs: https://code.claude.com/docs/en/overview, https://docs.anthropic.com/en/docs/intro
- OpenAI Codex manual / Codex Docs: https://developers.openai.com/codex
- Google Gemini / Workspace / Firebase: https://ai.google.dev/gemini-api/docs/models, https://developers.google.com/workspace/sheets/api/guides/batchupdate, https://firebase.google.com/docs/hosting
- Microsoft Azure AI Foundry: https://learn.microsoft.com/en-us/azure/ai-foundry/
- Meta Llama: https://llama.developer.meta.com/docs/overview
- Amazon Bedrock: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
- Apple Machine Learning / HIG: https://developer.apple.com/machine-learning/, https://developer.apple.com/design/human-interface-guidelines/
- xAI / Grok: https://docs.x.ai/docs
- Kimi / Moonshot AI: https://platform.moonshot.ai/docs/
- MiMo: https://github.com/XiaomiMiMo/MiMo
- DeepSeek API Docs: https://api-docs.deepseek.com/
- BytePlus / Seedance: https://docs.byteplus.com/en/docs, https://seed.bytedance.com/en/seedance
- GitHub Actions / Issues / Projects: https://docs.github.com/actions
- Slack Developer Docs: https://docs.slack.dev/
- Notion API: https://developers.notion.com/reference/intro
- Obsidian Help: https://help.obsidian.md/
- Unity Docs: https://docs.unity.com/
- Figma API: https://www.figma.com/developers/api
- Canva Connect APIs: https://www.canva.dev/docs/connect/
- Reddit API: https://www.reddit.com/dev/api/
- InsForge: https://docs.insforge.dev/introduction
- Firecrawl Docs: https://docs.firecrawl.dev/
- Discord Developer Docs: https://discord.com/developers/docs/intro
- Stripe Docs: https://docs.stripe.com/
- Supabase Docs: https://supabase.com/docs
- お名前.com ヘルプ/ドメインガイド: https://www.onamae.com/guide/
