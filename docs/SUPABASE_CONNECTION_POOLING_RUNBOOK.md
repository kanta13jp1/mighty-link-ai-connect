# Supabase 接続プール運用 Runbook (T759)

作成日: 2026-06-14  
オーナー: Codex レーン  
対象: Firebase Cloud Functions / Cloud Run 経由の FastAPI (`src/app.py`) から Supabase PostgreSQL への接続

---

## 目的

Firebase Cloud Functions / Cloud Run の水平スケール時に、各インスタンスが PostgreSQL へ直接接続を乱立させないようにする。T795 で本番 `SUPABASE_DB_URL` は Supavisor pooler URL へ切替済みのため、T759 ではアプリ側に小さな再利用プール、pre-ping、recycle、非秘密の状態確認を組み込む。

## 公式 docs 反映メモ

2026-06-14 の作業開始時に以下を確認した。

- Firebase Functions は runtime options をコード側の正本にし、min/max instances などの scaling を制御する。
- Firebase Functions networking は呼び出しごとの新規 outbound connection を避け、persistent connection を維持して CPU 時間と接続 quota を抑える。
- Supabase は IPv6 非対応環境やサーバーレスでは Supavisor pooler を使う。transaction mode は `pooler.supabase.com:6543`、session mode は `pooler.supabase.com:5432` で判定する。
- Supabase の connection management は direct connection 数と Supavisor pool size の両方を監視し、アプリ側 pool は小さく保つ。

## 実装

`src/app.py` は `USE_SUPABASE=true` かつ `SUPABASE_DB_URL` が `postgres://` または `postgresql://` の場合、`psycopg2.pool.ThreadedConnectionPool` を遅延初期化する。

| 設定 | 既定値 | 説明 |
| --- | ---: | --- |
| `SUPABASE_DB_POOL_MIN` | `1` | 各 Functions/Cloud Run インスタンス内で保持する最小接続数 |
| `SUPABASE_DB_POOL_MAX` | `4` | 各インスタンス内の最大接続数。Supavisor 側の pool を前提に小さく保つ |
| `SUPABASE_DB_CONNECT_TIMEOUT_SECONDS` | `3` | startup / request hang を避ける接続 timeout |
| `SUPABASE_DB_POOL_RECYCLE_SECONDS` | `1800` | 長時間生存した pool を閉じて再作成する間隔 |
| `SUPABASE_DB_POOL_PRE_PING` | `true` | 借用時に `SELECT 1` で切断済み接続を検知する |
| `SUPABASE_DB_APPLICATION_NAME` | `mighty-skill-bridge-functions` | Supabase / Postgres 監視で識別する非秘密名 |

既存コードは `conn.close()` を各処理の `finally` で呼ぶ。T759 では `PooledPostgresConnection` アダプタでこれを pool 返却に変換しているため、呼び出し側の実装を広く書き換えない。

## 接続文字列ルール

本番は Supavisor transaction pooler を正とする。

```text
postgresql://postgres.<project-ref>:<password>@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```

禁止・注意:

- raw secret を docs / WBS / Sheets / Issue へ書かない。
- direct `db.<project-ref>.supabase.co:5432` は IPv6 非対応 runtime で到達不能になりやすいため、本番 Functions では使わない。
- transaction mode ではセッション固定の一時テーブル、長い transaction、prepared statement 依存を避ける。
- 長い migration / backup / restore はアプリ pool 経由ではなく、DB migration / backup runbook の専用手順を使う。

## 確認手順

ローカル単体:

```powershell
python -m pytest tests/test_supabase_connection_pool.py -q
```

全体:

```powershell
python -m pytest -q
```

本番/preview で Basic Auth 付きに確認する場合:

```powershell
Invoke-RestMethod https://<host>/api/db-test -Credential (Get-Credential)
```

返却される `pool` は非秘密情報だけを含む。

| フィールド | 期待 |
| --- | --- |
| `enabled` | `true` |
| `pooler_mode` | `supavisor_transaction` |
| `max_connections` | `4` など小さい値 |
| `pre_ping` | `true` |
| `direct_postgres_status` | `success` |

## 異常時の判断

| 状態 | 意味 | 対応 |
| --- | --- | --- |
| `pooler_mode=direct_ipv6_risk` | direct Supabase DB URL の可能性 | Supabase Dashboard の Transaction pooler URL に戻す |
| `direct_postgres_status=fallback_sqlite` | DB接続失敗後に SQLite fallback | Functions env / secret / Supavisor 設定を確認 |
| `direct_postgres_status=error` | DB疎通失敗 | エラーメッセージを secret 値なしで Issue に記録し、T761/T761_1 へ接続 |
| pool timeout / exhausted | インスタンス内同時処理が pool を超過 | Cloud Functions max instances / concurrency と `SUPABASE_DB_POOL_MAX` を同時に見直す |

## 関連

- [FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md)
- [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md)
- [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md)
- [INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md](INFRA_TELEMETRY_DASHBOARD_RUNBOOK.md)
