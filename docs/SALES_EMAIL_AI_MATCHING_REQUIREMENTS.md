# 営業メールAIマッチング MVP要件定義

- 作成日: 2026-06-17
- 関連WBS: T817, T817_1, T817_2, T817_3, T817_4, T817_5, T817_6, T817_7, T821
- 関連Issue: #104, #105, #106, #107, #109
- ステータス: MVP要件定義、T817_2の安全なファイル取り込みPoC、T817_3のSupabaseスキーマ/RLS/migration整備、T817_4のAI抽出deterministic fallbackまで完了。実装はT817_5以降で段階実施。

---

## 目的

小林社長との2026-06-17打ち合わせで、営業全員が見られる共有営業アドレスに毎日約1,000通届く営業メール、案件メール、要員情報メールから案件要件や人材情報を自動抽出し、エンジニアのスキル、経験、希望条件と照合するAIマッチング機能を最優先で開発する方針になった。

本機能は、従来の「スキルシートと案件文面を1件ずつ入力してマッチ度を見る」体験を、実運用に近い「大量メールから案件DBを作り、候補案件を自動リストアップする」体験へ拡張する。

文字起こし照合で確認した主要課題は、Javaのような単純検索では見つけやすい案件がある一方、SQLやOracleのような語はメール本文の広い箇所に出現しやすく、キーワード検索では過剰ヒットしてしまう点である。MVPでは、単語の有無ではなく、案件要件・人材要件・経験文脈を構造化して照合する。

---

## MVPスコープ

### 1. メール取り込み

- Gmail APIを使った共有営業アドレスの受信メール取得を第一候補にする。
- 初期PoCでは、`.eml`、`.txt`、CSVアップロードによる手動取り込みも許容する。
- 取り込み対象は案件紹介、要員募集、要員提案、スキル要件、単価、勤務地、稼働時期を含むBP各社からの一斉配信メール。
- OAuthトークン、メール本文、添付ファイルの扱いは最小権限とし、認証情報をリポジトリ、Sheets、Issue、NotebookLMへ記録しない。

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

T817_3で `docs/SALES_EMAIL_DATABASE_SCHEMA_RUNBOOK.md` を追加し、Supabase/PostgreSQL/SQLiteのmigration、synthetic seed、rollback、pytestを整備済み。Supabase側は全テーブルでRLSを有効化し、`anon` と `authenticated` の直接アクセスを `REVOKE ALL` した。T817_4/T817_5でAPI実装に合わせたサービス層ポリシーを追加するまでは、公開REST経由の読み書き用 `CREATE POLICY` は作らない。

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
- OAuth、Gmail、Supabase、Firebaseのシークレットは環境変数またはGoogle/GitHubのSecret管理に限定する。
- 解析ログにはメール本文全文ではなく、件数、処理結果、エラー種別、ハッシュ、抽出項目サマリを残す。
- 本番利用前に、保持期間、削除手順、アクセス権、監査ログ、バックアップ/復元を確認する。

---

## WBS分解

| WBS | 内容 | 完了条件 |
| --- | --- | --- |
| T817_1 | MVP要件定義・データモデル設計 | 本文書、議事録、課題、QA、Go/No-Goゲートへ反映済み |
| T817_2 | Gmail/ファイル取り込みPoC | 完了。`.eml`、`.txt`、CSVを安全に取り込み、送信者/正規化件名/本文ハッシュで重複排除し、本文全文・secret非保存をpytestで検証済み |
| T817_3 | Supabaseスキーマ/RLS/migration | 完了。9テーブル、RLS、anon/authenticated直アクセスREVOKE、synthetic seed、rollback、SQLite fallback、pytestを整備済み |
| T817_4 | AI抽出パイプライン | 完了。案件要件、要員情報、スキルタグ、根拠抜粋、信頼度、deterministic fallbackを実装し、本文全文・個人連絡先・secret-like値の非出力をpytestで検証済み |
| T817_5 | マッチングAPI/UI | 条件検索、候補リスト、根拠表示が動く |
| T817_6 | 人間レビュー/評価ログ | 誤抽出修正、採用/却下、フィードバックが保存される |
| T817_7 | 本番運用hardening | 個人情報、監査、負荷、アカウント権限、Go/No-Goを確認済み |

---

## 公開判定への影響

本機能は2026-06-17打ち合わせで新たに最優先機能となったため、`public_paid_launch` の追加ゲートとする。限定デモは継続できるが、営業メールAIマッチングを売りにした一般公開、有償提供、営業利用は、T817_5からT817_7までの実装、レビュー、セキュリティ確認後に再判定する。

---

## 公式ドキュメント確認メモ

今回の要件化では、次の公式ドキュメントを参照した。

- Gmail API Guides: https://developers.google.com/workspace/gmail/api/guides
- Gemini API Models: https://ai.google.dev/gemini-api/docs/models
- Gemini API Context Caching: https://ai.google.dev/gemini-api/docs/caching
- Supabase Database Migrations: https://supabase.com/docs/guides/deployment/database-migrations
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Firebase Hosting Docs: https://firebase.google.com/docs/hosting
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions Docs: https://docs.github.com/actions
