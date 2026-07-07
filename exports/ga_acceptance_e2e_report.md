# GA受入E2E検証ログ (T845_1)

- レポートID: `GA_ACCEPTANCE_E2E_T845_1`
- 実施日: 2026-07-08
- 判定: **ok** (10/10 仮説PASS)
- スコープ: アプリ層の自動E2E受入。本番Supabase実書き込み確認（適性/勤怠/アナリティクス/営業メール系）はSUPABASE_DB_URL必須の人間工程（feedback/supportはT871で確認済み）。

## 10仮説検証（GA受入フロー）

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | ヘルスチェックとDB接続が正常（/api/health, /api/db-test） | PASS | health=200 db-test(auth)=200 mock=True |
| H2 | 認証境界: 運用系エンドポイントは未認証で401、正規認証で200 | PASS | 未認証summary=401 認証matches=200 |
| H3 | 社内診断（マッチング）フローがE2Eで動作（parse→match→一覧反映） | PASS | parse eng/job=200/200 match=200 db_match_id=1 listed=True |
| H4 | 同意強制: 同意なし/旧版の書き込みが全て400で拒否される | PASS | parse=400 match=400 stale=400 punch=400(全400期待) |
| H5 | 勤怠フローがE2Eで動作（打刻・勤務表解析・集計） | PASS | punch=200 timesheet=200(import_id=1) summary=200 |
| H6 | 営業メールAIマッチングの人間レビュー導線がE2Eで動作 | PASS | matches=200 summary=200 不正status=400(400期待) 正status=400(非500期待) |
| H7 | フィードバック・サポート問い合わせの保存/集計がE2Eで動作 | PASS | feedback=200(id=1) support=200 summary=200 |
| H8 | アナリティクス収集で個人情報最小化（pseudonym化・IP/生UA非保存）が機能 | PASS | event=200 privacy={'session_pseudonymized': True, 'ip_address_stored': False, 'raw_user_agent_stored': False, 'form_contents_stored': False} |
| H9 | 個人データエクスポートが厳格な本人認証を強制し、管理者ダッシュボードが動作する | PASS | export(厳格認証)=401(401/503期待) admin/usage=200 operations=200 |
| H10 | 本番appが稼働(health 200)し保護APIが認証壁(401)を返し、公開デモUIマーカーが存在する（外部証跡） | PASS | 本番health=200(200期待) 保護API=401(401期待) 公開デモmarkers=True |

## 残作業（T845の人間/認証情報依存工程）

- 本番Supabase実書き込み確認（適性/勤怠/アナリティクス/営業メール系9テーブル）: `SUPABASE_DB_URL` 設定のうえ運用者が実施。feedback/supportはT871で確認済み。
- Stripe課金導線: 社内GAは実課金なしのためT862へ移管（PUBLIC-09）。
- 実メール接続（営業メールAI）: T836接続情報受領後の追試（案A）。
- 最終UAT green判定と証跡のSheets同期・サインオフ: 7/8 15:00 定例（T819）。
