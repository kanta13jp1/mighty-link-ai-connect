# ポストモーテム: 本番Supabaseテーブル欠損による適性アンケート保存障害（R114）

作成日: 2026-07-04
担当レーン: VSCode + Claude Code
関連WBS: T865（復旧、完了） / T866（再発防止、Codex） / T845（UAT反映）
関連課題: R114（resolved） / Issue #157 / #158
関連docs: [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) / [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md)

---

## 事象

本番 `https://mightylink-app.com/` の従業員適性アンケート送信が 500 `{"detail":"Failed to store employee assessment response"}` で失敗した（2026-07-04 04:31 UTC、ユーザー報告）。

## タイムライン（UTC）

| 日時 | 出来事 |
| --- | --- |
| 2026-06-24 | T840/T841 で適性アンケート・勤怠のテーブルを migration 追加。**本番への適用は行われず** |
| 2026-06-27 | T800 で usage_analytics_events を migration 追加。同じく未適用 |
| 2026-07-04 04:26 | 本番コールドスタート。init_db（保険のDDL）は完了ログなし |
| 2026-07-04 04:31 | ユーザーがアンケート送信 → 500 ×2回。報告受領 |
| 2026-07-04 04:4x | Cloud Run ログで `relation "employee_assessment_responses" does not exist` を確認。migration 未適用と特定 |
| 2026-07-04 06:2x | ユーザー承認（案1）で未適用 migration 3件を適用。適用前の対象テーブルは **0件**（4テーブルすべて欠損） |
| 2026-07-04 06:29 | 合成データで検証: 適性アンケート success（response_id=1）、勤怠打刻 success（punch_id=1）。**復旧完了** |

## 根本原因

1. **migration の適用プロセス欠如**: `supabase/migrations/*.sql` は Supabase CLI での適用が前提だが、適用ステップがどのパイプラインにも組み込まれておらず、6/24 以降の3ファイルが本番へ届いていなかった（CI の DB Migration Validation は**検証のみ**）。
2. **アプリ側の保険が機能しない**: `init_db`（CREATE TABLE IF NOT EXISTS 一式）は FastAPI lifespan 起動時に daemon thread で実行されるが、Cloud Run（リクエスト課金）は**リクエスト処理中しか CPU を割り当てない**ため、バックグラウンドスレッドが完走しない。
3. **エラーの握りつぶし**: insert 例外は `{"id": 0}` に変換され、API は一律 500 を返す。エラー種別がクライアントにもトラッカーにも伝わらず、UAT 前の発見が遅れた。

## 影響

- 適性アンケート・勤怠打刻・利用アナリティクスの本番保存が、機能追加（6/24）以降ずっと失敗していた。適用前のテーブルが空だったことから、**本番で正常保存されたデータは存在しない**（送信者には毎回エラーが表示されており、サイレントなデータ消失ではない）。
- 診断・案件マッチング等の 6/24 以前のテーブルは影響なし。

## 再発防止（T866、Codexレーン）

1. init_db を lifespan の `yield` 前で**同期実行**する（コールドスタートは伸びるがスキーマ保証を優先）、または deploy パイプラインに `supabase db push`／migration 適用ステップを追加して DDL の正本を migration に一本化する。
2. ストレージ系 500 に内部エラー分類（relation_missing / connection / constraint）とログ相関 ID を付与し、検知性を上げる。
3. T845 UAT に「本番 postgres 実テーブルへの書き込み確認（適性・勤怠・アナリティクス・営業メール）」を明記（反映済み）。
4. 新規テーブル追加時のチェックリストに「migration 適用の実施証跡」を追加する。

## 教訓

- `CREATE TABLE IF NOT EXISTS` をアプリ起動時に流す設計は、サーバーレス実行環境（CPUスロットリング・即時スケールダウン）では保険にならない。スキーマ管理は deploy 時 migration に一本化する。
- 「検証のみのCI」と「適用する運用」の間のギャップは、タスク完了条件に「本番適用の証跡」を含めることで塞ぐ。
- 例外を握りつぶして汎用 500 に変換すると、原因特定がログアクセス保持者しかできなくなる。エラー分類は最初から仕込む。

## 再発防止の実装結果（2026-07-08・T866_1・Claude Code）

10仮説をテストで固定して実装した（tests/test_db_schema_guarantee.py 11件 + 全216テストgreen）。

1. `lifespan` は `yield` 前に `init_db` を完走させる方式へ変更（`asyncio.to_thread`）。コールドスタート直後・明示的init_dbなしでの初回POST成功をTestClientで実証。daemon thread起動関数は削除済み（復活防止テストあり）。
2. ストレージ系insert失敗10箇所の例外握りつぶしを廃止し、`record_storage_failure` が relation_missing / connection / constraint / unknown へ分類、相関ID（st-xxxx）をログと500 detailの両方へ付与（7エンドポイント適用）。SQL文・テーブル内部情報・個人データはクライアントへ出力しない。
3. DDL正本のmigration一本化と「新規テーブル追加チェックリスト（本番適用の実施証跡必須）」を docs/DB_MIGRATION_MANAGEMENT_RUNBOOK.md へ明文化（教訓4に対応）。
4. 残作業: 本番デプロイ後の T845 本番書き込み確認 green をもって T866 をクローズする（運用者工程）。
