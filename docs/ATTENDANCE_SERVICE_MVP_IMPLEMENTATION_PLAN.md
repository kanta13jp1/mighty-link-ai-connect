# 勤怠管理サービス MVP 実装計画

- 対象WBS: T951〜T955
- 方針承認日: 2026-08-14
- 実装基盤: FastAPI on Firebase / Cloud Run、Firebase Authentication、Supabase PostgreSQL
- 状態: 計画承認済み。T952以降の実装着手前

## 1. 決定

外部OSSへ全面移行せず、現行の勤怠モジュールを拡張する。

Frappe HR、Kimai、OrangeHRM、OCA/hr-attendance、solidtimeを比較した結果、外部OSSではFrappe HRが最も機能適合度が高かった。一方、Frappe/ERPNext基盤への再移行、GPL/AGPL系ライセンスの確認、日本向け運用ルールの追加が必要であり、現行FastAPI/Supabase基盤へ不足機能だけを追加する方がMVPの変更量と運用負荷が小さいと判断した。

外部OSSのソースコードは取り込まず、Frappe HRのEmployee Checkin、Attendance、Shift、Attendance Requestなどを境界条件とデータモデルの参考に限定する。

## 2. 現状と解消する問題

現行実装には以下が存在する。

- 出勤、退勤、休憩開始、休憩終了の打刻保存。
- CSV、XLSX、XLS勤務表のメモリ内解析。
- 勤務時間、残業、深夜、休日、異常件数の集計。
- 管理者による承認、拒否、サマリー取得。
- 識別子の仮名化、勤務表原本と元ファイル名の非保存。
- Supabase公開スキーマのRLS有効化と、`anon` / `authenticated` の直接権限剥奪。

MVP化に必要な未解決点は次のとおり。

1. 打刻と勤務表取込がFirebaseユーザー本人へ結び付いていない。
2. クライアントから送られた `employee_identifier` を本人識別として信用している。
3. 会社・部署などのテナント境界がなく、管理者サマリーが全件集計である。
4. 本人の月次表示、修正申請、変更履歴、月次締めがない。
5. サイト全体のBasic Authと、社員・管理者単位の認証・認可が分離されていない。

## 3. 認証・認可設計

### 3.1 リクエスト経路

1. ブラウザでFirebase Authenticationへログインする。
2. クライアントはFirebase IDトークンをHTTPSの `Authorization: Bearer` でFastAPIへ送る。
3. FastAPIはFirebase Admin SDKで署名、有効期限、発行者、対象プロジェクト、失効状態を検証する。
4. 検証済み `uid` を `ATTENDANCE_PSEUDONYM_SALT` でHMAC化し、直接識別子を保存しない安定キーへ変換する。
5. サーバー側の所属テーブルから `tenant_key`、`subject_pseudonym`、`role` を解決する。
6. 各クエリは必ず `tenant_key` と本人または許可された役割でスコープする。

サイト全体を閉じるBasic Authは当面維持するが、勤怠データの本人確認や権限制御には使用しない。

### 3.2 fail-closed要件

- 管理ランタイムでFirebase Admin SDKが利用できない場合は503。
- IDトークンがない、無効、期限切れ、失効済みの場合は401。
- 所属がない場合は403。
- `employee_identifier` で別社員を指定する互換経路は本番で無効化する。
- テスト用認証は `ATTENDANCE_AUTH_ALLOW_MOCK=1` の明示指定時だけ許可し、管理ランタイムでは常に拒否する。
- ロールはユーザーが変更できるFirebase `user_metadata` やリクエスト本文から取得しない。

## 4. データモデル

既存の直接RESTアクセス禁止方針を維持し、FastAPIサービス層でテナントスコープを必須化する。

### 4.1 新規テーブル

| テーブル | 目的 | 主な列 |
| --- | --- | --- |
| `attendance_tenants` | 会社単位の境界 | `tenant_key`, `status`, timestamps |
| `attendance_memberships` | Firebaseユーザーと勤怠主体・役割の対応 | `tenant_key`, `identity_pseudonym`, `subject_pseudonym`, `role`, `active` |
| `attendance_correction_requests` | 打刻修正申請と承認履歴 | `tenant_key`, `subject_pseudonym`, `target_event_id`, `requested_value`, `reason`, `status`, reviewer |
| `attendance_monthly_periods` | 月次提出、承認、締め状態 | `tenant_key`, `subject_pseudonym`, `year_month`, `status`, reviewer, timestamps |

### 4.2 既存テーブルの拡張

`attendance_punch_events` と `attendance_timesheet_imports` に以下を追加する。

- `tenant_key`
- `owner_pseudonym`
- `idempotency_key`
- `created_by_role`
- 必要な複合インデックス

既存レコードは単一のlegacy tenantへ移行し、移行完了まで管理者のみ閲覧可能とする。migrationには重複キー、NOT NULL移行、rollback可否の検証を含める。

## 5. MVP API

| API | 利用者 | 目的 |
| --- | --- | --- |
| `POST /api/attendance/punch` | 社員 | 本人の打刻。サーバー時刻とidempotency keyを使用 |
| `POST /api/attendance/timesheet/parse` | 社員 | 本人の勤務表取込。識別子はトークンから解決 |
| `GET /api/attendance/me/monthly` | 社員 | 自分の月次打刻、集計、承認状態を取得 |
| `POST /api/attendance/corrections` | 社員 | 打刻修正を申請 |
| `GET /api/attendance/admin/monthly` | manager/admin | 所属テナントの月次一覧 |
| `POST /api/attendance/admin/corrections/{id}/decision` | manager/admin | 修正申請を承認・拒否 |
| `POST /api/attendance/admin/periods/{id}/decision` | manager/admin | 月次提出を承認・差戻し・締め |
| `GET /api/attendance/admin/export.csv` | manager/admin | 締め済み月次データをCSV出力 |

既存のBasic Auth付きapprove/summaryは移行期間だけ残し、非推奨レスポンスヘッダーと監査ログを追加した後に廃止する。

## 6. 実装マイルストーン

### T952: 本人認証・テナント境界

- 厳格なFirebase IDトークン検証依存関係を実装。
- 所属・テナントmigrationを追加。
- 打刻と勤務表取込からクライアント指定の本人識別を排除。
- 欠落トークン、偽装ID、別テナントアクセス、role昇格を回帰テスト。

### T953: 本人用月次画面・修正申請

- 月次一覧、日跨ぎ、休憩、重複打刻の集計を実装。
- 修正申請と変更前後の監査証跡を追加。
- UIをFirebaseセッションと連動。

### T954: 管理者承認・月次締め・CSV

- manager/adminの所属テナント限定一覧を実装。
- 修正、差戻し、承認、締めの状態遷移を実装。
- 締め済み期間のCSV出力と再締め防止を追加。

### T955: パイロットUAT

- 5〜10名、1回の月次締めを合成データで実施。
- JST、日跨ぎ、休憩、二重送信、期限切れトークン、退職者無効化、別テナント拒否を検証。
- 月次CSVと期待値の差分0、未監査の更新0、テナント越境0をGo条件とする。

## 7. MVP対象外

- 給与計算、年末調整、有給残数管理。
- 複雑な交代制シフト、変形労働時間制の自動判定。
- GPS、顔認証、ICカード、ネイティブアプリ。
- ジョブカン、KING OF TIME、freeeとの本番OAuth接続。
- Frappe/Odooへの移行、外部OSSコードの直接取り込み。

T947の外部勤怠SaaS連携ドラフトは本MVPとは別スコープとする。認証情報未設定時のmock token、未認証provider API、OAuth state検証、token永続化・暗号化、各社公式API仕様が未確認の状態では本番へ含めない。

## 8. テストとリリースゲート

- 認証なし401、SDK利用不可503、所属なし403。
- 本人識別子の本文偽装が無効。
- employeeは本人のみ、manager/adminは所属テナントのみ閲覧可能。
- テナントAの認証でテナントBのIDを指定しても404または403。
- 同一idempotency keyの再送で二重打刻されない。
- すべての修正、承認、差戻し、締めにactorと時刻の監査記録がある。
- Supabase migration、SQLite fallback、既存勤怠APIの回帰テストがgreen。
- `python scripts/run_lane_preflight.py --full` がgreenになるまでcommit、push、deployしない。

## 9. 公式根拠

- Firebase Authentication: `https://firebase.google.com/docs/auth/admin/verify-id-tokens`
- Firebase custom claims: `https://firebase.google.com/docs/auth/admin/custom-claims`
- Supabase Row Level Security: `https://supabase.com/docs/guides/database/postgres/row-level-security`
- OpenAI Codex AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`

Firebase公式のとおり、クライアントが取得したIDトークンをHTTPSでバックエンドへ渡し、Admin SDKで検証した `uid` だけを本人識別の根拠にする。Supabase公開スキーマはRLSを有効にし、サービスキーやRLS bypass権限をブラウザへ公開しない。
