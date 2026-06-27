# 本番データ保持・削除・匿名化ポリシー全テーブル照合 Runbook

- 対象WBS: T847
- 完了日: 2026-06-27
- レーン: VSCode + Codex / VSCode + Claude Code
- 技術前提: Firebase Hosting / Firebase Functions, Supabase PostgreSQL, FastAPI, Google Workspace Sheets
- 関連: T742, T748, T756, T781, T817, T840, T841, T842, T846, PUBLIC-13

## 結論

T847では、現行サイトで作成済みのSupabaseテーブル、SQLite fallbackテーブル、ユーザーデータエクスポート、削除請求、問い合わせ、営業メールAI、勤怠、社内アンケート、課金導線について、保持・削除・匿名化・RLS・原本非保存を横断照合した。

現時点の結論は次のとおり。

- 共有営業メール本文全文、勤務表CSV原本、元ファイル名、Stripe secret、OAuth token、API key、service account JSONはDB、GitHub、Sheets、docs、NotebookLMへ保存しない。
- `employee_assessment_responses`、`attendance_*`、`sales_email_*` は匿名キー、ハッシュ、redacted excerpt、集計値のみを保存する。
- 高感度の新規テーブルはSupabase RLSを有効化し、`anon` / `authenticated` の直接テーブル権限をrevoke済み、またはRLS有効かつ公開REST policyなしのAPI proxy限定運用とする。
- 本人確認付きセルフエクスポートは `GET /api/user-data/export` で実装済み。ただし旧デモテーブルの完全な本人スコープはT752の `owner_uid` / `tenant_id` 追加まで制限付きで扱う。
- 退会・完全削除はT742の契約を正本とし、一般公開前にはT752/T745/T798の認証・同意・法務ゲートと合わせて再検証する。
- T847は完了したが、`public_paid_launch` はT845/T850/T849/T852/T854などの残ゲート完了までNo-Goのまま維持する。

## 参照した正本

| 種別 | 正本 |
| --- | --- |
| WBS | `data/WBS.tsv`, `docs/WBS.md` |
| 削除請求 | `docs/USER_DATA_DELETION_FLOW.md` |
| ログ保持 | `docs/LOG_ROTATION_AND_RETENTION_RUNBOOK.md` |
| 監査ログ保護 | `docs/AUDIT_LOG_MASKING_AND_ENCRYPTION.md` |
| セルフエクスポート | `docs/USER_DATA_SELF_EXPORT_RUNBOOK.md` |
| 営業メールAI | `docs/SALES_EMAIL_*_RUNBOOK.md` |
| 社内アンケート | `docs/EMPLOYEE_ASSESSMENT_RESPONSE_RUNBOOK.md` |
| 勤怠 | `docs/ATTENDANCE_WORKFLOW_RUNBOOK.md` |
| サポート | `docs/SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md` |
| 課金 | `docs/STRIPE_CUSTOMER_PORTAL_RUNBOOK.md`, `docs/BILLING_AND_REFUND_POLICY.md` |
| DB migration | `supabase/migrations/*.sql` |

## 全テーブル保持・削除マトリクス

| 領域 | テーブル/保存先 | 保存するもの | 保存しないもの | 保持 | 削除/匿名化 | アクセス制御 | T847判定 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| アカウント | `profiles` | Firebase UID、氏名、メール、経歴profile | secret、支払情報 | 利用中 | 退会時に物理削除。関連 `matches` はcascade | RLSで本人のみ。削除はCloud Functions/service role経由 | 照合済 |
| マッチング | `matches` | fit score、score details、matched/missing skills | 原本ファイル、secret | 利用中 | `profiles` 削除に連動して物理削除 | RLSで本人のみ | 照合済 |
| AI監査 | `audits` | prompt/response監査、token数 | API key、OAuth token | 30日から90日を標準。障害時のみ延長 | match削除時は `match_id` null化またはT756方針で暗号化/削除 | RLS有効、公開REST policyなし | 照合済。T845で本番データ混入を再確認 |
| 使用量 | `usage_ledgers` | daily calls/tokens、limit state | 請求カード、secret | 課金/不正調査に必要な期間 | 退会処理では `user_id` 匿名化を先行。FK cascadeは最後の安全網 | RLSで本人のみ | 照合済 |
| フィードバック | `feedback_events` | rating、NPS、redacted comment、session id | 氏名、連絡先、secret | 180日。品質集計後は匿名集計へ移行 | `session_id` 単位削除またはコメント匿名化 | RLS有効、公開REST policyなし、API proxy経由 | 照合済 |
| サポート | `support_requests` | 問い合わせ分類、返信先、件名、本文、status | 添付原本、認証情報、カード情報 | 問い合わせ終了後180日。請求/法務は7年まで別管理 | 本人請求で本文削除または匿名化。会計証跡は個人識別子を外して保持 | RLS有効、公開REST policyなし、管理summaryはBasic Auth | 照合済 |
| 営業メール取込元 | `sales_mailbox_sources` | source key、source type、保持日数、metadata | mailbox password、OAuth token | 90日標準 | 取込元停止時にmetadata匿名化、必要に応じ削除 | RLS有効、anon/authenticated revoke | 照合済 |
| 営業メール | `sales_email_messages` | message/body hash、sender hash/domain、subject、redacted excerpt | メール本文全文、添付、送信者メール実値、認証情報 | 90日標準 | dedupe/evidence保持後にhashのみ残す。本文抜粋は削除可能 | RLS有効、anon/authenticated revoke | 照合済 |
| 営業メール抽出 | `sales_email_entities`, `project_requirements`, `talent_profiles_from_email`, `requirement_skill_tags` | redacted evidence、案件要件、匿名要員key、skill tags | 個人連絡先、メール本文全文、未redact根拠 | 180日または案件クローズ後90日 | 案件/要員キー単位で削除、または匿名集計だけ保持 | RLS有効、anon/authenticated revoke | 照合済 |
| 営業メール処理ログ | `email_parse_runs` | 件数、モデル名、fallback、error summary | 入力メール本文、secret | 90日 | 実メール接続後は古いrunを削除または集計化 | RLS有効、anon/authenticated revoke | 照合済 |
| 営業メールレビュー | `email_match_results`, `email_match_feedback` | match score、redacted evidence、レビュー結果 | 連絡先、本文全文、secret | 180日。営業判断後は集計化 | `match_key` / project / talent単位で削除 | RLS有効、anon/authenticated revoke、Basic Auth API経由 | 照合済 |
| 社内アンケート | `employee_assessment_responses` | subject pseudonym、部署bucket、自己申告値、redacted growth memo、同意version | 氏名、社員番号、心理/健康スコア、医療情報 | PoC中90日。利用継続時は同意versionごとに180日見直し | `subject_pseudonym` 単位で削除、`status=deleted` 証跡のみ可 | RLS有効、anon/authenticated revoke | 照合済 |
| 勤怠打刻 | `attendance_punch_events` | subject pseudonym、event type、recorded_at | 氏名、社員番号、GPS、secret | 労務確認に必要な期間。PoCは180日 | `subject_pseudonym` 単位削除。法定保存が必要な本連携は会社労務正本側で管理 | RLS有効、anon/authenticated revoke | 照合済 |
| 勤務表CSV解析 | `attendance_timesheet_imports` | file digest、拡張子、集計値、承認status | CSV原本、元ファイル名、生明細、PDF/OCR原本 | PoCは180日 | `subject_pseudonym` 単位削除。承認ログは匿名化可 | RLS有効、anon/authenticated revoke | 照合済 |
| Stripe Portal | Stripe Dashboard / API response | short-lived portal session、masked customer/subscription id preview | `STRIPE_SECRET_KEY`、カード番号、portal URLの長期保存 | Stripe正本に準拠。アプリ側は永続化しない | Stripe側の顧客/購読削除・請求証跡保持はT807/T791で再確認 | Firebase Auth、env gate、secret非記録 | 照合済。liveはT807までNo-Go |
| セルフエクスポート | `GET /api/user-data/export` | 本人メール一致support、session一致feedback、関連match data | 他人のデータ、認証なしexport | ダウンロード時のみ生成 | 生成ファイルは利用者端末のみ。GitHub/Sheets添付禁止 | Firebase ID token必須。mockは明示envのみ | 照合済 |
| ローカル/CI監査ログ | `data/audit/*.jsonl`, `logs/*`, `data/external_api_usage*.jsonl` | redacted event、API usage summary | raw secret、OAuth token、個人データ原文 | 7日超または10MB超で圧縮、90日で削除 | `scripts/rotate_runtime_logs.py` でgzip化/削除 | repo artifactsはsecret scan対象 | 照合済 |
| Google Cloud Logging | Firebase Hosting / Functions logs | アクセス/実行ログ | secret、本文全文 | `_Default` 30日、長期証跡は承認付きsink | retention bucket / GCS lifecycle | GCP IAM | 照合済 |

## 削除リクエスト処理順序

1. 本人確認: Firebase Auth ID token、または管理者代理の場合は `PERSONAL_INFO_DISCLOSURE_PROCEDURES.md` の本人確認を行う。
2. 対象キー特定: `firebase_uid`、メールアドレス、`session_id`、`subject_pseudonym`、`match_key` などの必要最小限のキーだけを扱う。
3. 原本系の削除: 営業メールredacted excerpt、問い合わせ本文、社員アンケートmemo、勤怠集計を対象単位で削除または匿名化する。
4. 利用量/請求系の匿名化: 会計・不正調査で保持が必要な行は個人識別子を外して保持する。
5. アカウント系の削除: `profiles` を物理削除し、Firebase Auth recordを削除する。
6. 証跡: 削除日時、担当者、対象キー種別、成功/失敗だけを監査ログへ残す。個人データ実値は記録しない。

## 運用禁止事項

- 勤務表CSV原本、営業メール本文全文、添付ファイル、メールアドレス実値、電話番号、Stripe secret、OAuth token、service account JSONをGitHub/Sheets/docs/NotebookLMへ貼らない。
- `SUPABASE_SERVICE_ROLE_KEY` をローカルメモ、Issue、Sheets、READMEへ記録しない。
- 削除確認のために本番個人データをサンプル化してコミットしない。
- AIモデルへ未redactの実メール本文や勤怠明細を送らない。

## T845/T849への申し送り

- T845のE2E/UATでは、削除・エクスポート・管理summary・営業メールレビュー・勤怠CSV解析のレスポンスに、本文全文、CSV原本、直接識別子、secret-like値が含まれないことを再確認する。
- T849のサイト開発完了総合判定では、本Runbookの対象テーブルがWBS完了時点のschemaと一致しているかを再実行する。
- T752で `owner_uid` / `tenant_id` を導入したら、本Runbookの `engineers` / `jobs` / `match_results` のエクスポート制約を更新する。

## 公式ドキュメント確認メモ

2026-06-27のT847反映では、Supabase RLS/production、Firebase Hosting/Functions、Google Cloud Logging retention、Google Sheets API batchUpdate、GitHub Actions/Projects、Stripe Customer Portal/Billing、OpenAI Codex、Anthropic Claude Code、Google Gemini、Microsoft Azure AI Foundry、Slack、Notion、Firecrawl、InsForge、Discord、Figma、Canva、Reddit、Unity、Apple Machine Learning/HIG、AWS Bedrock、Meta Llama、xAI、Kimi、MiMo、DeepSeek、BytePlus、お名前.comの公式情報を確認した。
