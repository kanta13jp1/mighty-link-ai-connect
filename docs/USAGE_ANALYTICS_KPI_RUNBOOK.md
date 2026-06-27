# T800 利用状況アナリティクス計測設計・運用ランブック

- WBS: T800
- 状態: 完了
- 更新日: 2026-06-27
- 対象: 公開デモ、Firebase Hosting 配信版、将来の本番サイト
- 実装: `POST /api/analytics/event`, `usage_analytics_events`, 管理ダッシュボード CSV

---

## 目的

公開デモと本番前検証で、どの画面や導線が使われているかを、個人情報を保存せずに確認できるようにする。WBSがすべて完了した時に開発完了と判断できるよう、利用実態KPIを管理ダッシュボードとSheets連携対象へ含める。

GitHub Pagesの静的公開デモでは同一オリジンにFastAPIが存在しないため、フロントエンドのイベント送信は404を出さないようにskipする。Firebase/Functions配信、ローカルFastAPI、将来の本番API同一オリジンでは送信する。

---

## 公式ドキュメント確認

2026-06-27のT800実装では、次の公式ドキュメントの方針を確認した。

- Firebase Analytics: `https://firebase.google.com/docs/analytics`
- Firebase Analytics events: `https://firebase.google.com/docs/analytics/ios/events`
- Supabase Row Level Security: `https://supabase.com/docs/guides/database/postgres/row-level-security`
- Supabase API security: `https://supabase.com/docs/guides/api/securing-your-api`
- Google Sheets API batchUpdate: `https://developers.google.com/workspace/sheets/api/guides/batchupdate`
- GitHub Projects API: `https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects`

Firebase Analyticsは将来のFirebase Hosting本番運用で利用候補に残す。ただし現時点では、公開デモの同意・最小化・Supabase監査を優先し、SDKの自動収集ではなくファーストパーティAPIで匿名イベントだけを収集する。

---

## 収集イベント

| event_name | 意味 | 主なmetadata |
| --- | --- | --- |
| `page_view` | ページ表示 | `surface` |
| `section_view` | 主要セクション表示 | `section_id` |
| `cta_click` | ボタン、アンカークリック | `element`, `element_id`, `href` |
| `form_submit` | フォーム送信開始 | `form_id` |
| `form_success` | フォーム処理成功 | API側の将来拡張用 |
| `form_error` | フォーム処理失敗 | API側の将来拡張用 |
| `dashboard_export` | 管理ダッシュボードCSV出力 | 管理者操作の将来拡張用 |

---

## 保存しない情報

- IPアドレス
- 生のUser-Agent
- 氏名
- メールアドレス
- 電話番号
- フォーム本文
- APIキー、token、secret、password
- URLクエリ文字列

セッションIDは `USAGE_ANALYTICS_PSEUDONYM_SALT` を使い、`usage-<digest>` に変換して保存する。ブラウザ側のlocalStorageにはランダムな匿名セッションIDだけを保存する。

---

## DBとRLS

Supabase migration:

- `supabase/migrations/20260627000200_usage_analytics_events.sql`

テーブル:

- `public.usage_analytics_events`

制御:

- `ALTER TABLE public.usage_analytics_events ENABLE ROW LEVEL SECURITY`
- `REVOKE ALL ON TABLE public.usage_analytics_events FROM anon, authenticated`
- `REVOKE ALL ON SEQUENCE public.usage_analytics_events_id_seq FROM anon, authenticated`

アプリケーション経由の集計APIだけで確認し、Supabase anon RESTから直接読ませない。

---

## API

### `POST /api/analytics/event`

リクエスト例:

```json
{
  "event_name": "page_view",
  "event_surface": "public_demo",
  "page_url": "/#survey-section",
  "session_id": "usage-local-random-id",
  "metadata": {
    "surface": "home"
  }
}
```

レスポンス例:

```json
{
  "status": "success",
  "event_id": 1,
  "event_name": "page_view",
  "privacy": {
    "session_pseudonymized": true,
    "ip_address_stored": false,
    "raw_user_agent_stored": false,
    "form_contents_stored": false
  }
}
```

---

## KPI

管理ダッシュボード `GET /api/admin/operations-dashboard` に次を追加した。

- `usage_analytics_events`
- `usage_events_last_7_days`
- `usage_unique_sessions_last_7_days`
- `usage_page_views`

CSV `GET /api/admin/operations-dashboard/report.csv` には、`usage_analytics`、`usage_analytics_event`、`usage_analytics_surface` 行を出力する。

---

## 運用

1. 公開デモまたは本番サイトで主要導線を操作する。
2. 管理者Basic認証で `/api/admin/operations-dashboard` を確認する。
3. 必要に応じて `/api/admin/operations-dashboard/report.csv` をダウンロードする。
4. 月次品質報告では、T800のKPIとWBS完了状況を合わせて確認する。
5. Firebase Analytics SDKへ移行する場合は、事前にプライバシーポリシー、同意UI、オプトアウト導線、BigQuery連携可否を再審査する。

---

## 検証

対象テスト:

- `tests/test_api.py::test_admin_operations_dashboard_requires_auth_aggregates_and_exports_csv`
- `tests/test_data_retention_runbook.py`

確認項目:

- 未認証で管理ダッシュボードを読めない
- 無効なイベント名を拒否する
- セッションIDが疑似ID化される
- IPアドレス、生User-Agent、フォーム本文を保存しない
- RLSとanon/authenticated revokeがmigrationに存在する
