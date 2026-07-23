# 営業メールAIマッチング MVP要件定義

- 作成日: 2026-06-17
- 関連WBS: T817, T817_1, T817_2, T817_3, T817_4, T817_5, T817_6, T817_7, T821, T824
- 関連Issue: #104, #105, #106, #107, #109, #110
- ステータス: MVP要件定義、T817_2の安全なファイル取り込みPoC、T817_3のSupabaseスキーマ/RLS/migration整備、T817_4のAI抽出deterministic fallback、T817_5の双方向検索API/UI、T817_6の人間レビュー/評価ログまで完了。T824で接続方式をGmail前提からプロバイダ中立へ補正。本番hardeningはT817_7で段階実施。

---

## 目的

小林社長との2026-06-17打ち合わせで、営業全員が見られる共有営業アドレスに毎日約1,000通届く営業メール、案件メール、要員情報メールから案件要件や人材情報を自動抽出し、エンジニアのスキル、経験、希望条件と照合するAIマッチング機能を最優先で開発する方針になった。

本機能は、従来の「スキルシートと案件文面を1件ずつ入力してマッチ度を見る」体験を、実運用に近い「大量メールから案件DBを作り、候補案件を自動リストアップする」体験へ拡張する。

文字起こし照合で確認した主要課題は、Javaのような単純検索では見つけやすい案件がある一方、SQLやOracleのような語はメール本文の広い箇所に出現しやすく、キーワード検索では過剰ヒットしてしまう点である。MVPでは、単語の有無ではなく、案件要件・人材要件・経験文脈を構造化して照合する。

---

## MVPスコープ

### 1. メール取り込み

- 受信環境は未確定のため、Gmail APIを前提にしない。Microsoft 365 / Exchange Online、Google Workspace / Gmail、汎用IMAP、POP3、Webhook/メール転送、ファイル監視のいずれかをヒアリング後に選定する。
- 必要な確認項目は [SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md](SALES_EMAIL_AUTO_INGEST_CONNECTION_CHECKLIST.md) を正本にする。
- 初期PoCでは、`.eml`、`.txt`、CSVアップロードによる安全なファイル取り込みを許容する。
- 取り込み対象は案件紹介、要員募集、要員提案、スキル要件、単価、勤務地、稼働時期を含むBP各社からの一斉配信メール。
- OAuthトークン、メールパスワード、アプリパスワード、API secret、メール本文、添付ファイルの扱いは最小権限とし、認証情報をリポジトリ、Sheets、Issue、NotebookLM、Slack、チャット本文へ記録しない。

### 1.1 1日1,000件規模の実営業メール取り込み要件（2026-07-22 社長定例決定事項・T910）

2026-07-22 の社長定例にて、お名前.com での営業メール転送設定（営業アドレス → 自社Googleアドレス）完了に伴い、**1日1,000件規模（月3万件）**の実営業メール全件取り込みが決定した。これに伴い、以下のスケール要件を策定・適用する。

1. **転送・POP3受入パイプライン**:
   - メール転送受入および POP3/IMAP 経由での全件取り込みバッチ処理を構築し、従来の数件規模から日次 1,000 件へのスケールに対応する。
2. **高速重複排除・並行処理**:
   - 送信者 + 正規化件名 + 本文SHA-256ハッシュによる `sales_email_messages` テーブルでのインデックス高速スキップを実施し、重複取り込みを 0.1 秒未満で排除。
3. **AI抽出・マッチング統計パイプライン**:
   - Gemini Flash 経由での非同期キューイング解析を導入し、AI抽出処理のレート制限回避および日別マッチング統計ダッシュボードへの即時反映を実現。


### 2. 正規化と重複排除

- メール件名、送信者、受信日時、本文ハッシュ、案件名候補を用いて重複を検出する。
- 署名、引用返信、フッター、配信停止文、過去スレッド引用を可能な範囲で除去する。
- 個人名、電話番号、メールアドレスなどの個人情報は、保存前に必要最小限へ抑える。

### 3. Supabaseデータモデル

初期MVPでは次のテーブルを想定する。

| テーブル | 用途 |
| --- | --- |
| `sales_email_messages` | 取り込んだ営業メールのメタ情報、本文ハッシュ、必要最小限の本文 |
| `sales_mailbox_sources` | 共有営業アドレス、手動アップロード、将来の連携元などの取り込み元 |
| `sales_email_entities` | メールから抽出した案件、要員、会社、スキル、条件などの正規化単位 |
| `project_requirements` | AIまたは人間レビューで確定した案件要件 |
| `talent_profiles_from_email` | メール由来の要員情報、スキル、稼働条件、根拠抜粋 |
| `requirement_skill_tags` | SQL、Oracle、Java、AWS、PM、設計などのスキルタグ |
| `email_parse_runs` | 取り込み、抽出、エラー、モデル、処理時間の実行ログ |
| `email_match_results` | 案件とエンジニアのマッチ結果、スコア、根拠 |
| `email_match_feedback` | 人間レビュー結果、修正タグ、採用/却下理由 |

T817_3で `docs/SALES_EMAIL_DATABASE_SCHEMA_RUNBOOK.md` を追加し、Supabase/PostgreSQL/SQLiteのmigration、synthetic seed、rollback、pytestを整備済み。Supabase側は全テーブルでRLSを有効化し、`anon` と `authenticated` の直接アクセスを `REVOKE ALL` した。T817_5の候補検索APIは、Git管理されたsanitized extraction reviewを読むだけで、Supabaseへ匿名REST直書きしない。T817_6でBasic Auth付き人間レビューAPI、`email_match_feedback` 保存、redacted評価ログを追加済み。実メール接続後の保持/削除、監査、負荷、権限運用はT817_7で確認する。

### 4. AI抽出項目

AI抽出では、最低限次の項目を構造化する。

- メール種別: 案件紹介、要員提案、要員募集、その他
- 案件名候補
- 要員名または匿名化された要員識別子
- 業務内容
- 必須スキル
- 尚可スキル
- 技術カテゴリ: 言語、DB、クラウド、OS、ツール、工程、業務領域
- 単価、精算幅、支払条件
- 勤務地、リモート可否、出社頻度
- 稼働開始時期、期間、稼働率
- 商流、年齢制限、国籍制限、面談回数などの注意条件
- メール由来の根拠抜粋
- 抽出信頼度

T817_4で `docs/SALES_EMAIL_EXTRACTION_PIPELINE_RUNBOOK.md`、`src/sales_email_extract.py`、`scripts/extract_sales_email_requirements.py` を追加し、案件要件、要員情報、スキルタグ、根拠抜粋、信頼度を構造化するdeterministic fallbackを実装済み。AIの出力はそのまま確定情報にせず、人間レビューで修正できる前提にする。

### 5. マッチング

初期MVPでは、次の2方向を対象にする。

1. **エンジニア/経歴書から案件を探す**
   - スキルシート、経験、希望条件を入力し、共有営業アドレスに届いた案件メールDBから候補案件を提示する。
2. **案件要件から人材を探す**
   - 案件要件、必要スキル、単価、勤務地、稼働時期を入力し、蓄積済みの要員情報やエンジニアDBから候補人材を提示する。

スコアリング観点は次の通り。

- 必須スキル一致
- 尚可スキル一致
- 経験年数や工程経験の一致
- 希望勤務地、リモート条件、稼働時期の一致
- 単価や商流条件の許容範囲
- 不一致理由とリスク

結果画面では、スコアだけでなく、メール本文由来の根拠と不一致理由を表示する。営業判断の補助であり、自動決定にはしない。

### 6. UI/API

- メール取り込み状況、解析済み件数、未レビュー件数を確認できる。
- スキル、勤務地、リモート、単価、期間で案件をフィルタできる。
- エンジニアを選ぶと、関連案件の候補と根拠を一覧表示できる。
- 案件を選ぶと、候補人材または要員情報の候補と根拠を一覧表示できる。
- 誤抽出や不要案件を人間が修正、却下、再解析できる。

### 7. セキュリティ、個人情報、運用

- メール本文には個人情報、商流情報、非公開案件情報が含まれるため、公開デモやNotebookLM資料へ本文全文を転載しない。
- OAuth、IMAP/POP3、Microsoft Graph、Gmail、Webhook、Supabase、Firebaseのシークレットは環境変数、Google Secret Manager、GitHub Secrets、または会社指定のパスワード管理ツールに限定する。
- 解析ログにはメール本文全文ではなく、件数、処理結果、エラー種別、ハッシュ、抽出項目サマリを残す。
- 本番利用前に、保持期間、削除手順、アクセス権、監査ログ、バックアップ/復元を確認する。

### 8. リアルタイム自動通知・Slack/Teams連携仕様（Pro/Enterprise向け拡張機能）

1日1,000件規模の実営業メール受入パイプライン（T910）において、営業チームの即時対応力を強化するための通知仕様を定義する。

1. **スコア80%以上即時カード通知**:
   - AI抽出・マッチングスコアが **80% 以上** の高マッチ度案件・人材が検出された場合、指定の Slack / Teams Webhook チャンネルへリアルタイムに通知カードを送信。
   - 通知カードには、案件名/人材識別子、マッチ度スコア、AI抜粋根拠、およびワンクリックで詳細確認・レビューできるリンクを含める。
2. **毎朝9:00 日次サマリダイジェスト**:
   - 毎朝 9:00 に前日取り込んだ全メール（約1,000件）の抽出件数、最高マッチ件数、未対応件数の「日次要約サマリ」を自動投稿。
3. **過剰通知防止（スパム対策）**:
   - スコア 80% 未満のメールは即時通知を行わず、日次ダイジェストおよびダッシュボード上でのフィルタ検索のみで扱うことで、チャネルの通知過多を防止する。

---

## WBS分解

| WBS | 内容 | 完了条件 |
| --- | --- | --- |
| T817_1 | MVP要件定義・データモデル設計 | 本文書、議事録、課題、QA、Go/No-Goゲートへ反映済み |
| T817_2 | ファイル取り込みPoCと重複排除 | 完了。`.eml`、`.txt`、CSVを安全に取り込み、送信者/正規化件名/本文ハッシュで重複排除し、本文全文・secret非保存をpytestで検証済み |
| T817_3 | Supabaseスキーマ/RLS/migration | 完了。9テーブル、RLS、anon/authenticated直アクセスREVOKE、synthetic seed、rollback、SQLite fallback、pytestを整備済み |
| T817_4 | AI抽出パイプライン | 完了。案件要件、要員情報、スキルタグ、根拠抜粋、信頼度、deterministic fallbackを実装し、本文全文・個人連絡先・secret-like値の非出力をpytestで検証済み |
| T817_5 | マッチングAPI/UI | 完了。条件検索、候補リスト、根拠表示、CSV出力が動く |
| T817_6 | 人間レビュー/評価ログ | 完了。採用/却下/要確認/補正、redactedレビュー履歴、DB保存、Markdown/JSON評価ログが動く |
| T817_7 | 本番運用hardening | 未着手。実メール接続後の個人情報最小化、監査、負荷、アカウント権限、Go/No-Goを確認する |
| T824 | 自動取り込み接続方式チェックリスト | 完了。受信環境を推測せず、Microsoft Graph / Gmail API / IMAP / POP3 / Webhook / ファイル監視別の必要情報とSecret管理ルールを整理済み |

---

## 公開判定への影響

本機能は2026-06-17打ち合わせで新たに最優先機能となったため、`public_paid_launch` の追加ゲートとする。限定デモは継続できるが、営業メールAIマッチングを売りにした一般公開、有償提供、営業利用は、T817_7の実メール接続後の運用hardening、セキュリティ確認後に再判定する。

---

## 公式ドキュメント確認メモ

今回の要件化では、次の公式ドキュメントを参照した。

- Microsoft Graph messages: https://learn.microsoft.com/en-us/graph/api/user-list-messages
- Microsoft Graph delta query for messages: https://learn.microsoft.com/en-us/graph/delta-query-messages
- Microsoft Graph Outlook change notifications: https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview
- Gmail API Guides: https://developers.google.com/workspace/gmail/api/guides
- Gmail API Push Notifications: https://developers.google.com/workspace/gmail/api/guides/push
- IMAP4rev2 RFC 9051: https://datatracker.ietf.org/doc/html/rfc9051
- Amazon SES receiving email: https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html
- Gemini API Models: https://ai.google.dev/gemini-api/docs/models
- Gemini API Context Caching: https://ai.google.dev/gemini-api/docs/caching
- Supabase Database Migrations: https://supabase.com/docs/guides/deployment/database-migrations
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Firebase Hosting Docs: https://firebase.google.com/docs/hosting
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions Docs: https://docs.github.com/actions
