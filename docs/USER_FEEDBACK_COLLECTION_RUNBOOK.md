# User Feedback Collection Runbook (T763)

作成日: 2026-06-16  
対象: 診断結果評価ボタン / Net Promoter Score / Supabase集計連携

## 目的

診断結果画面で利用者の「役に立った / 改善したい」とNPSスコアを収集し、Mighty Skill-Bridgeの診断精度、説明品質、運用品質の改善材料として蓄積する。

## 公式Docs確認

2026-06-16 のセッション開始時点で、以下の公式Docsを確認した。

- Firebase Hosting / Cloud Functions: https://firebase.google.com/docs/hosting / https://firebase.google.com/docs/functions
- Supabase Data API / Row Level Security / JavaScript insert: https://supabase.com/docs/guides/api / https://supabase.com/docs/guides/database/postgres/row-level-security / https://supabase.com/docs/reference/javascript/insert
- Google Sheets batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions: https://docs.github.com/en/actions

## 実装概要

### フロントエンド

`index.html` の診断結果レポートにフィードバック帯を追加した。

- 評価: `helpful` / `not_helpful`
- NPS: 0〜10
- 補足コメント: 任意、最大1000文字
- 紐づけ: `/api/match` の `db_match_id`
- セッション識別子: localStorageのランダムID

静的GitHub Pages環境では `/api/feedback` が存在しないため送信失敗表示になる。本番Firebase Functions環境ではFastAPI endpointにPOSTされる。

### API

`src/app.py` に以下を追加した。

- `POST /api/feedback`
  - 公開送信用
  - レート制限: expensive API枠
  - rating / nps_score / comment length を検証
- `GET /api/feedback/summary`
  - Basic Auth必須
  - 総件数、rating別件数、NPS平均、直近イベントを返す

### データベース

`feedback_events` テーブルを追加した。

- `match_result_id`: `match_results.id` への参照
- `rating`: `helpful` / `not_helpful`
- `nps_score`: 0〜10
- `comment`, `source`, `page_url`, `session_id`, `metadata`, `created_at`

追加ファイル:

- `db/migrations/postgres/20260616000000_feedback_events.sql`
- `db/migrations/sqlite/20260616000000_feedback_events.sql`
- `supabase/migrations/20260616000000_feedback_events.sql`

Supabase側はRLSを有効化し、匿名REST公開ポリシーは作成しない。フィードバック送信はFastAPI経由に限定する。

## 運用手順

1. 本番反映後、診断結果画面で評価を送信する。
2. 管理者は `GET /api/feedback/summary` をBasic Auth付きで確認する。
3. 月次品質レポート（T764/T808）へNPS平均、否定評価比率、代表コメントを転記または自動集計する。
4. 明確な不具合・改善要望は `data/issues_tracker.tsv` と GitHub Issues へ登録する。

## 確認コマンド

```powershell
python -m pytest tests/test_api.py tests/test_db_migration_management.py
python scripts/manage_db_migrations.py validate --engine sqlite
python scripts/manage_db_migrations.py validate --engine postgres
python scripts/manage_db_migrations.py validate --engine supabase
```

## プライバシーと注意点

- コメント欄には個人情報を入力しない前提でUI/運用を案内する。
- 管理者向け集計APIはコメント全文ではなく `comment_excerpt` を返す。
- Supabase anon RESTから直接読ませないため、RLSポリシーは追加しない。
- 将来T800のイベント計測導入時に、個人識別子ではなくセッション単位の匿名集計へ寄せる。

## 後続タスクへの接続

- T790: 問い合わせフォーム/サポート導線へ、否定評価時の問い合わせ誘導を追加できる。
- T778: SLA/品質ビューにNPS平均と否定評価率を追加できる。
- T800: Firebase Analytics / Supabaseイベント計測のKPI設計に統合する。
- T808: 月次品質レポート自動配信へNPS集計を接続する。
