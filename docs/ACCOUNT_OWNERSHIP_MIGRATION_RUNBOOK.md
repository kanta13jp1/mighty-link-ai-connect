# 会社アカウント移行準備ランブック

作成日: 2026-06-19  
対象: Mighty-Link AI Connect / Mighty Skill-Bridge  
関連WBS: T818, T823  
関連課題: R76  

## 目的

現在は開発速度を優先し、一部の開発・運用環境を梅澤個人アカウントで作成している。正式運用、有料化、社内引き継ぎの前に、GitHub、Firebase/GCP、Supabase、AI開発ツール、ドキュメント基盤を会社所有、会社請求、会社管理の権限へ移すための準備状態を確定する。

T818では実移管そのものではなく、移管対象、順序、権限、請求、secret、検証、ロールバックを整理する。実移管はT823で別タスクとして扱う。

## 現状の所有・請求棚卸し

| 領域 | 現状 | 目標状態 | T818での判断 |
| --- | --- | --- | --- |
| ドメイン | `mightylink-app.com` はお名前.comで取得。現ドメイン単体の費用は0円 | 会社管理のレジストラ/請求へ集約、DNS変更権限を複数名で保持 | T823で移管可否と支払方法を確認 |
| ホスティング/バックエンド | Firebase Hosting / Firebase Functions / GCP。現状は梅澤個人アカウント起点のプロジェクト | 会社Google Workspaceまたは会社Cloud Identity組織配下、会社請求 | FirebaseはGoogle CloudプロジェクトとしてIAM/請求を移す |
| HTTPS証明書 | Firebase Hostingが自動発行、`https://mightylink-app.com/` は疎通済み | 証明書自動更新はFirebase管理を継続 | 移管時もDNSとFirebase Hosting設定を維持 |
| DB | Supabase。現状は梅澤個人アカウント起点 | 会社Supabase Organizationへプロジェクト移管、会社請求、MFA必須 | Supabase公式のProject Transferで実施 |
| ソースコード | GitHubリポジトリは梅澤個人アカウント管理 | 会社GitHub Organizationへ移管、複数Owner、Actions secretsを組織/環境単位へ再登録 | GitHubの個人リポジトリ移管手順で実施 |
| WBS/課題/QA | Google Workspace Sheets。会社提供Googleアカウント `k-umezawa@ml-mightylink.com` で同期 | 会社Workspaceの共有ドライブまたは会社管理ファイルへ集約 | 既存同期は会社Googleアカウントで稼働中 |
| NotebookLM | 会社提供Googleアカウントで使用 | 会社Workspace上のNotebookLM/Drive資料として継続 | docs同期対象に含める |
| 開発AI/運用ツール | Antigravity、Claude Code、Codex、Slack、Notion、Obsidianは暫定的に梅澤個人アカウント、個人課金を含む | 会社管理アカウント、会社請求、退職/権限変更時に継続できる構成 | T823で契約/管理者/支払方法を切替 |
| Stripe | 有料化前。審査/請求設定はT791以降 | 会社名義、会社銀行口座、会社税務情報で運用 | 個人アカウントに本番売上を紐づけない |

## 公式ドキュメント確認メモ

- GitHubは、個人所有リポジトリをOrganizationへ移管できる。ただし、移管先でリポジトリ作成権限が必要で、移管後はOrganization側の既定権限が適用される。
- FirebaseプロジェクトはGoogle Cloudプロジェクトでもあり、IAM、請求、プロジェクトID/番号、削除影響はGoogle Cloudと共有される。
- Firebaseの権限変更にはOwnerまたは `resourcemanager.projects.setIamPolicy` 相当の権限が必要。
- FirebaseのSpark/Blazeはプロジェクト単位で適用され、Cloud BillingをリンクするとBlazeへ移行する。
- SupabaseはProject Transferで別Organizationへ移管できる。Ownerは全権限、Administratorは組織設定更新、外部組織へのプロジェクト移管、新Owner追加などができない。
- GitHub Actions secretsはリポジトリ、環境、Organization単位で管理できるため、移管時に値をGitへ書かずに再登録する。
- Firebase HostingのカスタムドメインSSL証明書はFirebaseが自動でプロビジョニングするため、移管時はDNS、Hostingサイト、ドメイン検証状態を壊さないことを最優先にする。

## 移行前チェックリスト

### 1. 会社側の受け皿を作る

- 会社GitHub Organizationを作成または既存Organizationを指定する。
- Organization Ownerを2名以上にする。
- 会社GCP/Cloud Billingアカウントを用意し、請求先、予算アラート、支払責任者を明確にする。
- 会社Supabase Organizationを作成し、Ownerを2名以上にする。
- 会社Slack/Notion/Obsidian/Figma/Canva/Stripeなど、利用継続するツールの管理者と請求先を決める。
- Google Workspaceの共有ドライブまたは管理フォルダを用意し、WBS、課題管理表、QA表、NotebookLM同期資料の所有場所を決める。

### 2. secretとOAuthを棚卸しする

実値は記録しない。名前、保管場所、再発行先、切替担当だけを管理する。

| 種別 | 主な対象 | 実施内容 |
| --- | --- | --- |
| GitHub Actions secrets | `GEMINI_API_KEY`, `SUPABASE_DB_URL`, Firebase/GCP関連、Slack webhook等 | OrganizationまたはEnvironment secretとして再登録し、旧値は切替後に失効 |
| Google OAuth | `client_secret.json`, `authorized_user.json` | 会社Googleアカウントで再認証し、`verify_google_workspace_account.py` で実行主体を確認 |
| Firebase/GCP | サービスアカウント、CI用認証、Hosting/Functions deploy権限 | 会社Organization配下のIAMへ移し、個人Owner依存を削除 |
| Supabase | DB URL、service role key、anon key、migration権限 | 会社Organization移管後にキーを再発行し、アプリ/CI/ローカルの参照を更新 |
| Stripe | test/live keys、Webhook secret | 会社名義アカウントで本番キーを発行し、個人アカウントの本番売上化を避ける |

### 3. バックアップと復旧点を作る

- GitHub: `main` と `master` を同期し、移管前の最新commit hashを記録する。
- Firebase/GCP: Hosting release、Functions設定、環境変数、IAMロール、Billing状態をスクリーンショットまたはCLI出力で保存する。secret値は保存しない。
- Supabase: migration履歴、schema dump、RLS policy、Edge Functions、storage bucket設定を確認する。個人情報を含むデータdumpは取得しないか、必要最小限かつ暗号化された社内管理場所に限定する。
- Google Workspace: WBS URL、NotebookLM同期docs、Drive共有状態を確認する。
- DNS: お名前.comのDNSレコード、Firebase Hostingのカスタムドメイン状態、TLS証明書CN/発行者、A/CNAME/TXT/CAAの状態を記録する。

## 推奨移行順序

1. 会社側の管理者/請求/2名Owner体制を作る。
2. Google WorkspaceのWBS、課題管理表、QA表、NotebookLM資料を会社管理フォルダへ集約する。
3. GitHub Organizationへリポジトリを移管し、branch protection、Actions、Pages、Project、Issues、Secretsを確認する。
4. Firebase/GCPのIAMに会社管理者を追加し、Billingを会社請求へ切替える。問題がなければ個人Owner依存を外す。
5. Supabaseプロジェクトを会社OrganizationへTransferし、DB URLやservice role keyを再発行する。
6. CI/CD、公開デモ、Firebase Hosting、mightylink-app.com、WBS同期、Calendar同期、NotebookLM同期を一括検証する。
7. Antigravity、Claude Code、Codex、Slack、Notion、Obsidian、Figma、Canva、Stripeを会社契約/会社管理へ順次切替える。
8. 移管完了後、個人アカウントに残る権限を最小化し、非常時Owner/Break-glassアカウントを会社側で管理する。

## ロールバック方針

- GitHub移管後にActions/Pages/Projectが壊れた場合は、Organization内で権限とSecretsを復元し、移管前リモートURLを参照してローカルからpush可能か確認する。リポジトリを個人へ戻す判断は最後の手段にする。
- Firebase/GCP請求切替で課金/権限が壊れた場合は、個人Ownerを残した状態で会社請求リンクとIAMだけ戻し、Hosting/Functions releaseは移管前のreleaseへ戻す。
- Supabase移管で接続が壊れた場合は、旧接続情報を短時間だけ復元し、会社Organization側でキー再発行/接続文字列更新をやり直す。旧キーは復旧後に必ず失効する。
- DNS/SSLが壊れた場合は、Firebase Hostingの要求レコードを再確認し、お名前.com側のA/CNAME/TXT/CAAを移管前記録へ戻す。
- どのロールバックでも、secret値をIssue、Sheets、NotebookLM、Slack/Notion本文へ貼らない。

## 受入基準

T818は以下を満たした時点で完了とする。

- 現状の個人/会社アカウント境界が棚卸し済み。
- GitHub、Firebase/GCP、Supabase、Google Workspace、NotebookLM、AI開発ツール、Stripe、ドメインの移行順序が定義済み。
- secret/OAuth/請求/権限/ロールバックの確認項目が定義済み。
- 実移管をT823としてWBSへ追加し、T818と実施タスクを分離済み。
- WBS、課題管理表、QA表、GitHub Issue、NotebookLM/Sheets/Calendar同期に反映済み。

## T823実施時の検証コマンド

```powershell
python scripts/verify_google_workspace_account.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://mightylink-app.com/
```

必要に応じて、`https://mightylink-app.com/` のTLS疎通、Firebase Hosting release、Supabase接続、GitHub Actionsの直近成功Runも確認する。

## 参照

- [GitHub Docs: Transferring a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)
- [GitHub Docs: Moving your work to an organization](https://docs.github.com/en/account-and-profile/how-tos/account-management/moving-your-work-to-an-organization)
- [GitHub Docs: Using secrets in GitHub Actions](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)
- [Firebase Docs: Understand Firebase projects](https://firebase.google.com/docs/projects/learn-more)
- [Firebase Docs: Manage project access with Firebase IAM](https://firebase.google.com/docs/projects/iam/overview)
- [Firebase Docs: Firebase pricing plans](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans)
- [Firebase Docs: Connect a custom domain](https://firebase.google.com/docs/hosting/custom-domain)
- [Google Cloud Docs: Enable, disable, or change billing for a project](https://docs.cloud.google.com/billing/docs/how-to/modify-project)
- [Supabase Docs: Project Transfers](https://supabase.com/docs/guides/platform/project-transfer)
- [Supabase Docs: Access Control](https://supabase.com/docs/guides/platform/access-control)
