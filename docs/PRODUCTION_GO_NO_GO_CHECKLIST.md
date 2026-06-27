# 本番リリース Go/No-Go 判定チェックリスト (T746)

作成日: 2026-06-17
オーナー: VSCode + Codex レーン
関連: [WBS.md](WBS.md) / [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md) / [PRODUCTION_DOMAIN_SETUP_GUIDE.md](PRODUCTION_DOMAIN_SETUP_GUIDE.md)

---

## 目的

T746 は、Mighty-Link AI Connect を本番公開または有償提供へ進める前に、判定基準・証跡・承認者・未完了ゲートを一元化するためのタスクである。

本チェックリストでは、次の2つを明確に分ける。

- `controlled_demo`: CEO共有済みの管理下デモ、社内確認、限定説明に使える状態
- `public_paid_launch`: 一般ユーザー向け公開、有償プラン開始、Stripe課金を含む状態

---

## 現時点の判定

| Scope | 判定 | 理由 |
| --- | --- | --- |
| `controlled_demo` | `GO` | GitHub Pages公開デモ、本番URL、問い合わせ窓口、DR/Incident/Rollback、監視・クォータRunbookの証跡が揃っている |
| `public_paid_launch` | `NO_GO` | リリースノート/バージョニング運用、T805外部疑似診断、T835公開URLヘッダhardening、T846最新ユーザー/管理者docs、T847全テーブル保持/削除照合、T745ドラフト規約同意UI/APIガード、T777法定4ページリンク統合は整備済みだが、法務/CEO承認、正式アカウント同意履歴、オンボーディング、Stripe課金、負荷テスト、営業メールAIマッチング本番hardening、全機能最終UAT、会社運用引継ぎ、Firebase CI/CD、課題/QA棚卸し、サイト開発完了総合判定が未完了 |

つまり、現状は「社長説明・限定デモは継続可。一般公開・有償ローンチは未承認」である。

2026-06-17の小林社長・梅澤打ち合わせで、共有営業アドレスに毎日約1,000通届く営業メールから案件要件や要員情報を抽出し、エンジニア候補と照合するAIマッチング機能が最優先開発項目になった。文字起こし照合では、エンジニア/経歴書から案件を探す方向に加えて、案件要件から候補人材を探す逆方向も要望として確認した。これに伴い、営業メールAIマッチングMVPは `public_paid_launch` の追加ゲートとして扱う。T817_6までで安全な取り込みPoC、DB/RLS、抽出、候補検索、人間レビュー保存は完了した。限定デモのGo判定は維持するが、本機能を売りにした一般公開、有償提供、営業利用はT817_7の実メール接続後hardening完了後に再判定する。

2026-06-19にT806を前倒し完了し、`VERSION`、`CHANGELOG.md`、GitHub Releases用のRunbook、release versioning verifierを整備した。初回タグ `v0.1.0-controlled-demo.1` は管理下デモ用prereleaseであり、GAや有償ローンチを意味しない。

2026-06-21にT805を前倒し完了し、OWASP WSTG / OWASP ZAP baseline相当の非破壊疑似診断を `scripts/run_external_pentest_review.py` で実施した。CEO共有GitHub Pages URLと `mightylink-app.com` は到達可能で、High 0、secret-like値露出 0 を確認した。

2026-06-23にT835を前倒し完了し、Firebase Hosting本番URLへ CSP / X-Content-Type-Options / Referrer-Policy / Permissions-Policy / frame protection / HSTS を設定した。デプロイ後の `https://mightylink-app.com/` 再診断も HIGH 0 / MED 0 / LOW 0 / INFO 0 でPASS。GitHub Pagesは任意HTTPヘッダを設定できないため、CEO向けcontrolled demo mirrorとして制約を [EXTERNAL_PENTEST_RUNBOOK.md](EXTERNAL_PENTEST_RUNBOOK.md) に記録した。PUBLIC-01はPASSへ戻す。

2026-06-25にT844としてWBS工程網羅性監査（第3回）を実施し、全WBS完了をサイト開発完了条件にするための横断ゲートを追加した。T845全機能E2E/UAT、T846ユーザー/管理者docs最終更新、T847全テーブル保持/削除照合、T848外部SaaS/AIモデル棚卸し、T850会社運用引継ぎ、T849サイト開発完了総合判定が完了するまで、`public_paid_launch` とサイト開発完了宣言はNo-Goとする。PUBLIC-13を追加済み。

2026-06-26のWBS再レビュー後、main CIのFirebase deployでWorkload Identity Federation経由ADCがFirebase CLIに認識されず、legacy `FIREBASE_TOKEN` も再認証期限切れであることを確認した。docs/data/exportsのみの変更ではFirebase deployをskipする暫定ガードを入れたが、これは本番デプロイ成功の代替ではない。T852で会社管理のWIF/service account/secret経路を再構成し、アプリ変更時のmain deploy greenを確認するまで、`public_paid_launch` とサイト開発完了宣言はNo-Goとする。PUBLIC-14を追加済み。

同じく2026-06-26の第2セッションで、T849の完了条件にGitHub Issues/Projectだけでなく、Sheets正本である課題管理表とQA表の開発必須open/未回答ゼロ確認を明示する必要があると確認した。この時点でPUBLIC-15を追加し、T854で `data/issues_tracker.tsv`、`data/qa_tracker.tsv`、Google Sheets、GitHub Issues/Projectを突合する方針にした。

2026-06-27にT846としてユーザー操作ガイド・管理者Runbook・FAQを現行機能へ全面更新し、T847として [DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md) を追加した。T847では `profiles` / `matches` / `audits` / `usage_ledgers`、feedback/support、`sales_email_*`、`employee_assessment_responses`、`attendance_*`、Stripe Portal、セルフエクスポート、ローカル/Cloud Loggingについて、保持・削除・匿名化・RLS・原本非保存を照合した。

同じく2026-06-27にT848として [AI_SAAS_SERVICE_FREEZE_RUNBOOK.md](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md) を追加し、Anthropic/OpenAI/Google/Microsoft/Meta/Amazon/Apple/xAI/Kimi/MiMo/DeepSeek/BytePlus/GitHub/Slack/Notion/Obsidian/Unity/Figma/Canva/Reddit/InsForge/FireCrawl/Discord/Stripe/Supabase/Firebase/お名前.com の採用/非採用、モデル/API、fallback、secret管理、会社請求移管状態を凍結した。これによりPUBLIC-13内のT846/T847/T848部分は完了したが、T845/T850/T849が残るため `public_paid_launch` とサイト開発完了宣言はNo-Goのまま維持する。

2026-06-27にT745として [LEGAL_CONSENT_UI_AND_API_RUNBOOK.md](LEGAL_CONSENT_UI_AND_API_RUNBOOK.md) を追加し、`index.html` / `src/index.html` のAnalyze実行前にサービス利用規約・プライバシーポリシー・特商法表記・課金規約/返金ポリシーのドラフト確認チェックを必須化した。`src/app.py` では `/api/parse` と `/api/match` が `MSB-LEGAL-2026-06-DRAFT` の同意バージョンを検証し、未同意または旧バージョンを400で拒否する。あわせてフッター常時リンクを補強したためPUBLIC-05とPUBLIC-07はPASSへ更新する。ただしT798の法務本文確定、T804の価格確定、T752のユーザー別同意履歴が残るため `public_paid_launch` はNo-Goのまま維持する。

同じく2026-06-27にT854として [ISSUE_QA_BLOCKER_AUDIT_2026-06-27.md](ISSUE_QA_BLOCKER_AUDIT_2026-06-27.md) を追加し、課題管理表とQA表の未分類open/未回答を棚卸しした。`scripts/audit_issue_qa_blockers.py --fail-on-blockers` により、課題ブロッカー0件、QAブロッカー0件を `exports/issue_qa_blocker_audit.*` へ証跡化したためPUBLIC-15はPASSへ更新する。ただし、T845/T849/T850/T852や法務・価格・課金・負荷・実メール接続などの残ゲートは別管理であり、`public_paid_launch` はNo-Goのまま維持する。

同じく2026-06-27のT854クローズアウト中に、Public Uptime Monitorと `python scripts/check_uptime_targets.py` が販売URL `https://mightylink-app.com/` のDNS解決失敗を検出した。GitHub Pages公開デモとFirebase Hosting default URLはOKだが、特商法販売URLとして扱うcustom domainがstrict HTTPS監視でgreenになるまで、`public_paid_launch` とサイト開発完了宣言はNo-Goとする。T855、R103、QA-83、PUBLIC-16を追加し、詳細は [CUSTOM_DOMAIN_UPTIME_INCIDENT_2026-06-27.md](CUSTOM_DOMAIN_UPTIME_INCIDENT_2026-06-27.md) を正本とする。

同じく2026-06-27にT856として `scripts/diagnose_custom_domain_dns.py` を追加し、RDAPとGoogle/Cloudflare Public DNSの診断を `exports/custom_domain_dns_diagnostic.*` へ証跡化した。結果はRDAP `client hold` とPublic DNS `NXDOMAIN` であり、T855ではお名前.com側のhold解除、権威DNS委任、Firebase Hosting required records再確認を優先する。T856は完了だが、PUBLIC-16はT855復旧まで `BLOCKED` のまま維持する。

---

## 正本と生成物

| 種別 | パス / 同期先 | 用途 |
| --- | --- | --- |
| 判定基準TSV | [../data/release_go_no_go_criteria.tsv](../data/release_go_no_go_criteria.tsv) | Go/No-Go基準の正本 |
| 自動レビュー | [../scripts/generate_production_go_no_go_review.py](../scripts/generate_production_go_no_go_review.py) | TSVとWBSを突合し、判定レポートを生成 |
| Markdown証跡 | [../exports/production_go_no_go_review.md](../exports/production_go_no_go_review.md) | 人間レビュー用 |
| JSON証跡 | [../exports/production_go_no_go_review.json](../exports/production_go_no_go_review.json) | CI/自動処理用 |
| リリース運用証跡 | [../exports/release_versioning_review.md](../exports/release_versioning_review.md) | CHANGELOG / VERSION / GitHub Releases境界の確認 |
| Google Sheets | `リリース判定` タブ | WBS/課題/QAと同じスプレッドシートへ同期 |

WBSの正本は [../data/WBS.tsv](../data/WBS.tsv) であり、[WBS.md](WBS.md) は `scripts/generate_wbs_md.py` で再生成する。

---

## 判定ルール

| 状態 | 意味 | リリース判断 |
| --- | --- | --- |
| `PASS` | 証跡があり、要求状態を満たしている | Go要件を満たす |
| `WARNING` | 進行可能だが注意点が残る | Go with warnings |
| `HUMAN_GATE` | CEO、法務、開発責任者など人間承認が必要 | 承認完了までNo-Go |
| `BLOCKED` | 必須タスクまたは証跡が未完了 | No-Go |
| `N/A` | 対象外 | 判定から除外 |

`public_paid_launch` は、`BLOCKED` が0件、かつ `HUMAN_GATE` が承認済みになるまで `NO_GO` とする。

---

## 未完了ゲート

| WBS | 内容 | 現在の扱い |
| --- | --- | --- |
| T752 | ユーザーオンボーディング / アカウント登録・アクティベーション | `BLOCKED` |
| T776 / T791 | Stripe課金設計・Billing Meters/Webhook検証 | `BLOCKED` |
| T770 | 同時100ユーザー想定の負荷テスト | `BLOCKED` |
| T817_7 | 共有営業メールAIマッチングMVPの個人情報/監査/負荷確認、実メール接続後の運用hardening | `BLOCKED` |
| T845 | 全機能本番受入E2E/UAT最終再検証 | `BLOCKED` |
| T850 | 会社運用引継ぎリハーサル・権限棚卸し・Break-glass確認 | `BLOCKED` |
| T849 | サイト開発完了総合判定・WBS全完了証跡化・GAリリース閉鎖 | `BLOCKED` |
| T852 | Firebase/GitHub Actionsの本番デプロイ認証経路を会社管理のWIF/service account/secret経路へ再構成し、アプリ変更時のmain deploy greenを証跡化 | `BLOCKED` |
| T855 | mightylink-app.com DNS/HTTPS死活監視復旧とお名前.com/Firebase Hostingレコード再確認 | `BLOCKED` |
| T798 | 利用規約・プライバシーポリシー法務確認 | `HUMAN_GATE` |
| T804 | 料金プラン・価格設定のCEO承認 | `HUMAN_GATE` |

完了済みの公開前ゲート: T806 リリースノート・SemVer・git tag・GitHub Releases運用、T805 外部ペネトレーション疑似診断（High 0 / secret-like値露出 0）、T835 公開URLセキュリティヘッダhardening、T745 ドラフト規約同意UI/APIガード、T777 法定4ページとフッター常時リンク、T846 ユーザー/管理者docs最終更新、T847 全テーブル保持・削除・匿名化照合、T848 AIモデル・外部SaaS・連携サービスGA凍結。

---

## 承認プロセス

1. 各レーンが担当ゲートの証跡を `docs/`、`exports/`、GitHub Issue、WBSへ残す。
2. Codexレーンが `python scripts/generate_production_go_no_go_review.py` を実行し、判定レポートを再生成する。
3. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` で `リリース判定` タブへ同期する。
4. 完了済みWBSイベントは `python scripts/sync_wbs_to_calendar.py` でGoogle Calendarから削除する。
5. `public_paid_launch` の `BLOCKED` が0件になった後、CEO、法務、開発責任者が最終承認する。
6. Go判定時は、known-good commit、Firebase Hosting release、Cloud Run revision、Supabase backup/PITR時刻、rollback担当者を記録してから本番反映する。

---

## 技術前提

- レジストラ: お名前.com
- ホスティング / バックエンド: Firebase Hosting、Firebase Functions、GCP
- DB: Supabase
- ソースコード管理: GitHub
- WBS/課題/QA/リリース判定: Google Workspace Sheets
- 会社アカウント移行: T818で準備ランブックを整備済み。実移管、請求切替、個人Owner依存の解消はT823で実施する。
- リリース運用: T806で `CHANGELOG.md`、`VERSION`、SemVer、git tag、GitHub Releasesのprerelease運用を整備済み。GAタグはpublic_paid_launchの全ゲート通過後に発行する。

---

## 公式ドキュメント確認メモ

2026-06-27時点の確認対象:

- Firebase Hosting / Functions: https://firebase.google.com/docs/hosting / https://firebase.google.com/docs/functions
- Firebase CLI / Hosting GitHub integration: https://firebase.google.com/docs/cli / https://firebase.google.com/docs/hosting/github-integration
- Gmail API: https://developers.google.com/workspace/gmail/api/guides
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions / OIDC for Google Cloud / workflow triggers: https://docs.github.com/actions / https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform / https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- GitHub Releases: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- SemVer 2.0.0: https://semver.org/
- Supabase: https://supabase.com/docs/guides/getting-started
- Stripe rate limits / API運用: https://docs.stripe.com/rate-limits
- Stripe Docs: https://docs.stripe.com/
- 消費者庁 特定商取引法関連情報: https://www.caa.go.jp/policies/policy/consumer_transaction/specified_commercial_transactions/
- OpenAI Codex manual: `C:\Users\kanta\AppData\Local\Temp\openai-docs-cache\codex-manual.md`
- Claude Code / Codex / Gemini / Notion / Slack など、プロジェクト運用で使うAI・開発ツールの公式Docs

公式Docs確認は、判定基準そのものではなく「現在の実装・同期・運用手順が各サービスの現行ガイドに反していないか」を確認するために行う。
