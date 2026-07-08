# DB接続負荷分散設計（リードレプリカ・プールサイズ最適化）

- 作成日: 2026-07-08
- 対象WBS: T782（設計と負荷テスト検証）
- 担当: Claude Code（Codexレーン巻き取り）
- 証跡: `exports/read_load_distribution_simulation.{json,md}`（10仮説・10/10 PASS）/ `exports/load_test_100_users_2026-07-08.json`
- シミュレーションハーネス: `scripts/simulate_read_load_distribution.py` / テスト: `tests/test_read_load_simulation.py`
- 関連: [SUPABASE_CONNECTION_POOLING_RUNBOOK.md](SUPABASE_CONNECTION_POOLING_RUNBOOK.md) / [LOAD_TEST_100_USERS_REPORT_2026-07-01.md](LOAD_TEST_100_USERS_REPORT_2026-07-01.md) / [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)

## 1. 公式docs確認結果（2026-07-08）

Supabase Read Replicas（https://supabase.com/docs/guides/platform/read-replicas）:

- レプリカごとに**専用エンドポイント**（DB接続文字列・API）が発行され、Supavisor接続プールもレプリカ単位で提供される。
- **Load balancer endpoint** は GET リクエストを最寄りDBへ、非GETをPrimaryへ自動ルーティングする（REST API経由のみ）。
- レプリケーションは**非同期**でありlag（複製遅延）が存在する。SELECT専用。Auth/Storage/RealtimeはPrimary固定。

## 2. 現行構成（確認済み事実）

- アプリ側プール: `psycopg2 ThreadedConnectionPool`、インスタンスあたり `SUPABASE_DB_POOL_MIN=1` / `SUPABASE_DB_POOL_MAX=4`、recycle 1800s、pre-ping、Supavisor transaction mode（`pooler.supabase.com:6543`）検出。
- transaction pooler制約（session state不可）へは**非抵触**（SET/LISTEN/PREPARE/DECLARE 使用ゼロをコード走査で確認）。
- Cloud Run/Functionsの `maxInstances` は**未設定**（下記 §5 で明示設定を推奨）。

## 3. ルート分類（レプリカ振り分け設計の基礎）

`src/app.py` の実APIサーフェスから静的分類（証跡JSONに全ルート記録）:

| 分類 | 件数 | 備考 |
| --- | --- | --- |
| read（GET /api/*） | 21（60%） | |
| write（POST等） | 14 | Primary固定（原理上） |
| **レプリカ安全read** | **17（read内81%）** | summary/KPI/管理ダッシュボード/health/エクスポート系。複製遅延に耐える |
| **Primary固定read** | 4 | `/api/matches` `/api/engineers` `/api/jobs`（直前POSTの結果を即読むread-after-write）+ `/api/auth/me` |

## 4. シミュレーション結果（Erlang C・実測トラフィック基準）

基準: 実測バースト 144.1 req/s（100ユーザー×3リクエスト/2.08s、T858 probe）、DB接続占有 25ms/req（保守設定・感度分析付き）。

| 負荷 | primary単独(c=4/台) | レプリカoffload後 | 必要インスタンス数(利用率≤80%) |
| --- | --- | --- | --- |
| 1x (144 req/s) | 利用率90%・P95待ち174ms（予算300ms内） | 利用率46% | 2台 → 1台 |
| 10x (1441 req/s) | **飽和** | 飽和（1台では） | **12台 → 6台（半減）** |

- **プール待ち予算**: P95プール待ち ≤ 300ms（P95 SLA 3000msの10%）と定義。
- 1xバーストでも1インスタンスは利用率90%と余裕が薄い。**水平スケール（Cloud Runの自動インスタンス追加）が第一の吸収機構**であり、プールを太らせるのではなくインスタンスを増やす。
- T866（lifespan同期化）適用後の実負荷テスト再実行: errors=0、p95=1113ms、SLA green（回帰なし）。

## 5. プールサイズ安全式（Supavisor予算）

```
maxInstances × SUPABASE_DB_POOL_MAX ≤ Supavisorクライアント接続予算(≈200・Microティア目安)
推奨: maxInstances=20 × POOL_MAX=4 = 80 ≤ 200（2.5倍の余裕）
```

- **推奨アクション**: Functions/Cloud Run の `maxInstances` を明示設定する（現状未設定。無制限スケールはSupavisor接続を食い潰すリスク）。
- POOL_MAXを上げるより先にインスタンス数で並列度を確保する（transaction poolerが多重化するため、アプリ側プールは小さく保つ方針を維持）。

## 6. 段階的スケール計画（移行トリガー）

| Phase | トリガー | 施策 |
| --- | --- | --- |
| 0（現在・社内GA） | — | 現行構成で十分。`maxInstances=20` の明示設定のみ実施 |
| 1 | P95プール待ち>300ms または 利用率>80%が継続（SLA計測基盤T778のkpi_daily_response_timeで監視） | インスタンス上限を12台目安まで引き上げ（予算式内） |
| 2 | 有償公開後にアクセス5-10倍（T862判断と連動） | **リードレプリカ1台追加**。`SUPABASE_DB_READ_URL` を新設し、`get_db_connection(read_intent=True)` 拡張でレプリカ安全17ルートを振り分け（実装はこのトリガー発火時。必要台数が半減する効果はシミュレーション検証済み） |
| 3 | 複数リージョン/さらなる増加 | レプリカ複数台 + Load balancer endpoint（GET自動振り分け） |

- Phase 2実装時の注意: レプリカ接続もSupavisor経由（レプリカ専用プール）。read-after-write 4ルートは必ずPrimary。複製遅延の許容値は「summary/KPI系で数秒」を上限目安とし、超過時はPhase 2を見送る。

## 7. 監視・検証

- `/api/health` の `get_supabase_pool_status()` でプール設定・初期化状態を常時露出（非秘密のみ）。
- プール待ち/利用率の実測は T778 SLA計測基盤（`kpi_daily_response_time`）とuptime monitorで代替観測し、Phase 1トリガーを判定する。
- 本設計の再検証: `python scripts/simulate_read_load_distribution.py --fresh-load-json <最新負荷テストJSON> --fail-on-attention`
