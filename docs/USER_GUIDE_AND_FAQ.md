# Mighty Skill-Bridge ユーザー操作ガイド・FAQ・管理者Runbook

> 対象読者: 社内利用者、営業担当、人事/管理担当、システム管理者
> 最終更新: 2026-06-27
> バージョン: v1.3.0
> 関連WBS: T744 / T745 / T790 / T781 / T817 / T829 / T840 / T841 / T842 / T843 / T846

---

## 1. 現在の提供状態

Mighty Skill-Bridge は、エンジニアと案件のフィット分析を起点に、営業メールAIマッチング、社内向け適性・状況アンケート、勤怠CSV解析、管理者統合ダッシュボードを一つの社内業務画面にまとめたアプリです。

| 区分 | 現在の扱い |
| --- | --- |
| 管理下デモ | CEO共有済みの GitHub Pages URL で継続利用可 |
| 一般公開・有償ローンチ | Go/No-Go上は引き続き No-Go |
| 主な未完了ゲート | 法務本文確定、正式アカウント同意履歴、課金live検証、営業メール実接続hardening、全機能E2E/UAT、Firebase CI/CD本番デプロイ認証、会社運用引継ぎ |
| データ方針 | secret、実メール本文、CSV原本、直接識別子、契約金額実値をGitHub/Sheets/docs/NotebookLMへ記録しない |

アクセス先:

| 環境 | URL |
| --- | --- |
| CEO共有デモ | `https://kanta13jp1.github.io/mighty-link-ai-connect/` |
| 本番想定URL | `https://mightylink-app.com/` |
| ローカル開発 | `http://localhost:8000` |

GitHub Pages は静的デモです。フォームや管理APIはFirebase/FastAPI環境で有効になり、GitHub Pagesでは静的表示またはfallback表示になります。

---

## 2. 画面操作ガイド

### 2.1 社内向けナビゲーション

トップナビとフッターは次の内部セクションへ接続します。

| メニュー | アンカー | 用途 |
| --- | --- | --- |
| ホーム | `#top` | サービス概要と主要導線 |
| 適性アンケート | `#survey-section` | 社内向け自己申告フォーム |
| 勤怠管理 | `#attendance-section` | 打刻、勤務表CSV解析、承認 |
| 営業メールマッチング | `#matching-section` | 案件/人材候補の双方向比較 |
| 管理者ダッシュボード | `#admin-dashboard-section` | 診断、勤怠、営業メールAIの集約 |
| サポート | `#support` | 問い合わせ、データエクスポート導線 |

旧 `#join-us` などの外向けアンカーはT843で削除済みです。

### 2.2 AIフィット分析

エンジニア情報と案件情報を入力し、Skill / Culture / Growth / Performing の4軸でフィット度を確認します。

運用上の注意:

- Analyze実行前に、サービス利用規約、プライバシーポリシー、特商法表記、課金規約・返金ポリシーのドラフト確認チェックが必須です。未同意または古い同意バージョンの場合、`/api/parse` と `/api/match` は400で拒否します。
- AI結果は補助情報であり、採用、配属、契約可否の自動判断には使いません。
- Gemini APIが使えない場合は deterministic fallback でルールベース診断を継続します。
- 診断結果をSheetsやIssueへ転記する場合、氏名、連絡先、契約条件の実値を含めないでください。

### 2.3 営業メールAIマッチング

営業メールAIマッチングは、BP各社から届く案件メール/要員メールを安全に構造化し、案件から候補人材、人材から候補案件を双方向に探すための機能です。

現在できること:

1. sanitized extraction review をもとに候補を表示する。
2. スコア、スキル一致、条件一致、根拠、不一致理由を確認する。
3. `POST /api/sales-email/reviews` で採用、却下、要確認、補正レビューを保存する。
4. `GET /api/sales-email/reviews/summary` でレビュー状況を確認する。

まだ本番公開前に残ること:

- 実メールボックス接続方式の確定。
- Microsoft Graph、Gmail API、IMAP等のOAuth/管理者承認。
- 実メール接続後の保持、削除、監査、負荷、権限確認。

本文全文、BP担当者連絡先、候補者の直接連絡先、OAuth token、secretは同期成果物へ載せません。

### 2.4 社内向け適性・状況アンケート

`#survey-section` から、同意付きの自己申告フォームを送信します。

入力項目:

| 項目 | 扱い |
| --- | --- |
| 社内確認コード | salt付きハッシュで匿名キー化 |
| 部署カテゴリ | 粗いカテゴリとして保存 |
| モチベーション/カルチャー | 1から5の自己申告値 |
| 成長・支援メモ | メール、電話、secret-like値をredactして保存 |
| 同意 | 送信前に必須 |

この機能は精神状態や健康状態のAI診断ではありません。心理/健康スコア連携や外部サーベイ個人別データ連携は、R36/T838/T839の法務・ベンダー確認後に再判定します。

API:

- `POST /api/employee-assessment/responses`
- `GET /api/employee-assessment/responses/summary` Basic Auth必須

### 2.5 勤怠管理・勤務表CSV解析

`#attendance-section` から、簡易打刻と勤務表CSV解析を行います。

操作手順:

1. 社内確認コードを入力する。
2. 同意チェックを入れる。
3. 打刻ボタンで `clock_in` / `clock_out` / `break_start` / `break_end` を保存する。
4. CSVまたはテキストCSVを選択して勤務表を解析する。
5. 管理者はBasic Auth付きAPIで承認または却下する。

保存するのは匿名キー、集計値、承認ログです。CSV原本、PDF原本、元ファイル名、勤怠明細行、社員番号そのものは保存しません。PDF/OCRやジョブカン本連携はT823/T836後に再判定します。

API:

- `POST /api/attendance/punch`
- `POST /api/attendance/timesheet/parse`
- `POST /api/attendance/timesheet/approve` Basic Auth必須
- `GET /api/attendance/summary` Basic Auth必須

### 2.6 管理者統合ダッシュボード

`#admin-dashboard-section` では、管理者ユーザー名とパスワードを入力して実データ集計を読み込みます。認証情報はBasic Authヘッダー作成にのみ使い、localStorageやHTMLには保存しません。

API:

- `GET /api/admin/operations-dashboard?limit=20`
- `GET /api/admin/operations-dashboard/report.csv?limit=100`

表示/CSV出力するもの:

- 診断回答数、平均値、部署別件数。
- 勤怠打刻件数、勤務表取込件数、承認状態別件数。
- 営業メールレビュー件数、完了率、レビュー状態別件数。
- Basic Auth、CSV出力認証、redaction済み集計であることのsecurityフラグ。

表示/出力しないもの:

- 氏名、メールアドレス、電話番号、社員番号。
- 勤務表CSV/PDF原本、元ファイル名、明細行。
- 営業メール本文、個人連絡先。
- API key、password、token、secret-like値。

### 2.7 請求・解約導線

`/billing` では Stripe Customer Portal セッションAPIのdry-run検証ができます。

現在の扱い:

- `STRIPE_CUSTOMER_PORTAL_ENABLED=1` と `STRIPE_SECRET_KEY` が揃わない限り、Stripe外部通信は行いません。
- dry-runやpreviewではCustomer ID、Subscription IDをマスクします。
- live検証、Dashboard設定、Webhook確認はT807で実施します。

API:

- `POST /api/billing/customer-portal/session`

一般公開・有償ローンチまでは、請求や解約の実運用を開始しません。

### 2.8 サポート問い合わせ

`#support` のフォームから、一般、技術不具合、請求、個人情報、診断改善の問い合わせを送信します。フォーム送信が使えない静的デモ環境では、暫定窓口 `k-umezawa@ml-mightylink.com` へ連絡します。

SLA目安:

| 優先度 | 条件 | 初動 |
| --- | --- | --- |
| P1 | サービス全体停止、認証全断、個人情報漏えい疑い、重大な課金事故 | 30分以内 |
| P2 | AI診断不可、DB保存不可、技術不具合、個人情報/請求確認 | 当日から2時間以内 |
| P3 | 通常問い合わせ、Sheets/Calendar同期遅延、軽微なUI不具合 | 1営業日以内 |
| P4 | ドキュメント誤記、改善提案 | 2から5営業日以内 |

管理者確認API:

- `GET /api/support/summary` Basic Auth必須

### 2.9 ユーザーデータエクスポート

本人確認済みユーザーは `GET /api/user-data/export` でJSON形式のセルフエクスポートPoCを使えます。現行デモでは、本人メールに一致する問い合わせ、指定session_idに紐づくfeedback/match/engineer/jobを返します。

注意:

- Firebase Auth bearer token が必要です。
- デモの旧テーブルには恒久的な `owner_uid` がないため、T752完了前はPoC扱いです。
- エクスポートJSONをGitHub Issues、Sheets、Slack、NotebookLMへ添付しないでください。

---

## 3. FAQ

### Q1. いま一般公開や有償ローンチをしてよいですか？

いいえ。管理下デモはGoですが、`public_paid_launch` はNo-Goです。法務本文確定、正式アカウント同意履歴、Stripe live検証、負荷テスト、営業メール実接続hardening、全機能E2E/UAT、Firebase CI/CD本番デプロイ認証などが残っています。T745でドラフト規約への実行前同意UI/APIガードは実装済みですが、T798の法務確認とT752のユーザー別同意履歴は未完了です。

### Q2. 全ユーザーがBasic認証でログインしますか？

いいえ。トップ画面の通常利用はBasic認証前提ではありません。Basic Authは管理者summary、承認、統合ダッシュボード、CSVレポートなどの管理APIに限定します。

### Q3. 適性アンケートは健康状態や精神状態を診断しますか？

しません。Mighty Skill-Bridge本体は精神状態や健康状態をAI診断せず、本人同意のある業務支援用自己申告メタデータだけを最小保存します。外部サーベイの個人別心理/健康データ連携は法務・ベンダー確認後に再判定します。

### Q4. 勤務表はPDFでも解析できますか？

現時点ではCSVまたはテキストCSVだけです。PDF/OCRは原本保存や誤読のリスクがあるため、T841では対象外にしています。

### Q5. 営業メールAIマッチングは実メールへ接続済みですか？

まだ実メール接続後の本番hardeningは未完了です。T817_1からT817_6で要件、PoC、DB/RLS、抽出、双方向検索、人間レビューは整備済みですが、T817_7とT836で実メール環境、OAuth/管理者承認、保持/削除、監査、負荷、権限を確認します。

### Q6. Gemini APIが使えない場合でも動作しますか？

はい。deterministic fallbackにより、AI自然言語解析が使えない場合でもルールベースの抽出や診断を継続します。ただし、最終判断は常に人間が行います。

### Q7. 問い合わせや個人情報確認はどこで扱いますか？

アプリ内フォームまたは暫定メール窓口で受け付けます。管理者は `GET /api/support/summary` で件数、カテゴリ、優先度、抜粋だけを確認します。全文や添付ファイルをSheets/Issue/docsへ転記しないでください。

### Q8. 自分のデータを削除できますか？

削除請求はサポート窓口で受け付け、`USER_DATA_DELETION_FLOW.md` と `PERSONAL_INFO_DISCLOSURE_PROCEDURES.md` に従って本人確認、対象範囲確認、削除証跡の記録を行います。PoCやパイロット終了時は同意書に沿って削除します。

### Q9. 自分のデータをエクスポートできますか？

`GET /api/user-data/export` のPoCがあります。Firebase Authで本人確認したうえで、本人に紐づく問い合わせとsession_id由来の一部デモデータをJSONで取得します。公開・有償ローンチ標準機能化にはT752の所有者カラム整備が必要です。

### Q10. Stripe Customer Portalで解約できますか？

アプリ側APIとdry-run画面はT829で整備済みですが、live運用はT807完了後です。現時点で実課金や実解約の本番処理は開始しません。

### Q11. Google Sheets/Calendar同期に失敗した場合は？

まず `python scripts/verify_google_workspace_account.py` を実行し、必要なら `python scripts/verify_google_workspace_account.py --reauth` で `k-umezawa@ml-mightylink.com` を再認証します。OAuth tokenやclient secretは記録しません。

### Q12. Firebase CI/CDが失敗していても開発完了と言えますか？

いいえ。T852/PUBLIC-14で、アプリ変更を含むmain CIからFirebase Hosting/Functionsへ会社管理WIF/service account/secret経路でdeployできることを公開前必須ゲートにしています。

---

## 4. 管理者Runbook

### 4.1 システム構成

```text
Browser SPA / GitHub Pages controlled demo
  |
  +-- Firebase Hosting / Functions (FastAPI)
        |
        +-- Supabase PostgreSQL + RLS
        +-- SQLite fallback for local/dev safety
        +-- Gemini API / deterministic fallback
        +-- Stripe Customer Portal API gate
        +-- Google Workspace sync scripts
```

主要管理先:

| 項目 | 場所 |
| --- | --- |
| GitHub Actions | `https://github.com/kanta13jp1/mighty-link-ai-connect/actions` |
| 公開デモ | `https://kanta13jp1.github.io/mighty-link-ai-connect/` |
| 本番想定URL | `https://mightylink-app.com/` |
| WBS正本 | `data/WBS.tsv` |
| 課題管理表正本 | `data/issues_tracker.tsv` |
| QA表正本 | `data/qa_tracker.tsv` |
| リリース判定正本 | `data/release_go_no_go_criteria.tsv` |

### 4.2 障害時の一次確認

```powershell
gh run list --limit 5 --repo kanta13jp1/mighty-link-ai-connect
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/verify_google_workspace_account.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

### 4.3 管理API確認

Basic Authヘッダーを作ってsummary APIを確認します。認証情報は環境変数から読み、コマンド履歴やdocsへ実値を残しません。

```powershell
$pair = "$env:BASIC_AUTH_USERNAME`:$env:BASIC_AUTH_PASSWORD"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
Invoke-WebRequest -Uri "http://localhost:8000/api/admin/operations-dashboard" -Headers @{Authorization = "Basic $auth"} -UseBasicParsing
Invoke-WebRequest -Uri "http://localhost:8000/api/support/summary" -Headers @{Authorization = "Basic $auth"} -UseBasicParsing
```

### 4.4 Firebase CI/CD失敗

T852が完了するまでは、アプリ変更を含むmain pushでFirebase deployが失敗する既知リスクがあります。

確認手順:

```powershell
gh run list --limit 5
gh run view <run-id> --log-failed
```

原因がWIF/ADCまたはlegacy `FIREBASE_TOKEN`失効の場合は、GitHub Issue #139 / R100 / PUBLIC-14へ証跡だけを追記します。service account JSON、token、`.env`、Functions runtime secretの実値は記録しません。

### 4.5 日次・週次・月次運用

日次:

```powershell
python scripts/monitor_managed_agents_cost.py
python scripts/verify_google_workspace_account.py
```

週次:

```powershell
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

docs変更時:

```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
python scripts/generate_ceo_presentation_deck.py
python scripts/upload_notebooklm_docs_to_drive.py
```

### 4.6 エスカレーション

| 優先度 | 条件 | 対応 |
| --- | --- | --- |
| P1 | サービス全体停止、認証全断、個人情報漏えい疑い、重大な課金事故 | Incident Runbookに接続し、CEO/開発担当へ即時共有 |
| P2 | AI診断不可、DB保存不可、請求/個人情報確認 | 課題管理表とGitHub Issueへ起票 |
| P3 | Sheets/Calendar同期失敗、デプロイ遅延、通常問い合わせ | 次回開発セッションまたは定例で処理 |
| P4 | docs誤記、軽微UI、改善提案 | QA表または月次品質レポートへ集約 |

---

## 5. 関連ドキュメント

| ドキュメント | 内容 |
| --- | --- |
| [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) | Antigravity + Gemini / VSCode + Codex / VSCode + Claude Code の運用 |
| [SALES_EMAIL_AI_MATCHING_REQUIREMENTS.md](SALES_EMAIL_AI_MATCHING_REQUIREMENTS.md) | 営業メールAIマッチング要件 |
| [SALES_EMAIL_MATCHING_API_UI_RUNBOOK.md](SALES_EMAIL_MATCHING_API_UI_RUNBOOK.md) | マッチングAPI/UI |
| [SALES_EMAIL_HUMAN_REVIEW_RUNBOOK.md](SALES_EMAIL_HUMAN_REVIEW_RUNBOOK.md) | 人間レビュー保存 |
| [EMPLOYEE_ASSESSMENT_RESPONSE_RUNBOOK.md](EMPLOYEE_ASSESSMENT_RESPONSE_RUNBOOK.md) | 社内アンケート保存 |
| [ATTENDANCE_WORKFLOW_RUNBOOK.md](ATTENDANCE_WORKFLOW_RUNBOOK.md) | 勤怠打刻/CSV解析 |
| [ADMIN_OPERATIONS_DASHBOARD_RUNBOOK.md](ADMIN_OPERATIONS_DASHBOARD_RUNBOOK.md) | 管理者統合ダッシュボード |
| [LEGAL_CONSENT_UI_AND_API_RUNBOOK.md](LEGAL_CONSENT_UI_AND_API_RUNBOOK.md) | 規約同意UI/APIガード |
| [STRIPE_CUSTOMER_PORTAL_RUNBOOK.md](STRIPE_CUSTOMER_PORTAL_RUNBOOK.md) | Stripe Customer Portal dry-run/live準備 |
| [USER_DATA_SELF_EXPORT_RUNBOOK.md](USER_DATA_SELF_EXPORT_RUNBOOK.md) | ユーザーデータJSONエクスポート |
| [USER_DATA_DELETION_FLOW.md](USER_DATA_DELETION_FLOW.md) | データ削除フロー |
| [SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md](SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md) | サポート/SLA |
| [PRODUCTION_GO_NO_GO_CHECKLIST.md](PRODUCTION_GO_NO_GO_CHECKLIST.md) | 本番Go/No-Go判定 |
| [WBS.md](WBS.md) | WBS表示版 |

---

## 6. 公式ドキュメント確認メモ

2026-06-27のT846/T745更新では、Claude Code、OpenAI Codex、Google Gemini/Workspace、Firebase Hosting、Supabase、Stripe Billing、Microsoft Azure AI Foundry、AWS Bedrock、Kimi、BytePlus、Slack、Unity、Firecrawlなどの公式ドキュメントと、プロジェクト内Runbookを確認した。長い引用は残さず、管理APIの認証境界、規約同意UI/APIガード、redaction済み集計、Google Workspace同期、Stripe live gate、Firebase CI/CD未解決ゲート、secret非記録方針だけを本ガイドへ反映した。
