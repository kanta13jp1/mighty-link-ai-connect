-- Mighty-Link AI Connect Supabase performance diagnostic bundle
-- Task: T750
-- Read-only probes. Review generated output before taking maintenance action.
\pset pager off
\timing on

\echo '--- extension_status: Confirm whether pg_stat_statements, hypopg, and index_advisor are available.'
select extname, extversion
from pg_extension
where extname in ('pg_stat_statements', 'hypopg', 'index_advisor')
order by extname;

\echo '--- top_queries_by_total_time: Find high total-time statements that dominate DB work.'
select
  queryid,
  calls,
  round(total_exec_time::numeric, 2) as total_exec_time_ms,
  round(mean_exec_time::numeric, 2) as mean_exec_time_ms,
  rows,
  left(regexp_replace(query, '\s+', ' ', 'g'), 240) as query_sample
from pg_stat_statements
order by total_exec_time desc
limit 20;

\echo '--- top_queries_by_mean_time: Find statements with high per-call latency.'
select
  queryid,
  calls,
  round(mean_exec_time::numeric, 2) as mean_exec_time_ms,
  round(max_exec_time::numeric, 2) as max_exec_time_ms,
  left(regexp_replace(query, '\s+', ' ', 'g'), 240) as query_sample
from pg_stat_statements
where calls >= 5
order by mean_exec_time desc
limit 20;

\echo '--- sequential_scan_pressure: Identify tables where sequential scans dominate indexed scans.'
select
  schemaname,
  relname,
  seq_scan,
  idx_scan,
  n_live_tup,
  n_dead_tup,
  last_analyze,
  last_autoanalyze
from pg_stat_user_tables
where seq_scan > greatest(idx_scan * 2, 50)
order by seq_scan desc
limit 30;

\echo '--- unused_indexes: Find non-primary-key indexes with no scans, then review before dropping.'
select
  schemaname,
  relname as table_name,
  indexrelname as index_name,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
from pg_stat_user_indexes
where idx_scan = 0
  and indexrelname not like '%_pkey'
order by pg_relation_size(indexrelid) desc
limit 30;

\echo '--- large_indexes: List largest indexes for storage maintenance review.'
select
  schemaname,
  relname as table_name,
  indexrelname as index_name,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
from pg_stat_user_indexes
order by pg_relation_size(indexrelid) desc
limit 30;

\echo '--- vacuum_analyze_lag: Find tables that may need vacuum/analyze attention.'
select
  schemaname,
  relname,
  n_live_tup,
  n_dead_tup,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
from pg_stat_user_tables
where n_dead_tup > greatest(n_live_tup * 0.2, 1000)
order by n_dead_tup desc
limit 30;
