# Supabase Postgres Version Check

- Task: T828 (related: T811)
- Generated: 2026-06-21T07:46:40Z
- Status: needs_credentials
- PG14 EOL date: 2026-07-01
- SQL: `select version();`

## Results

| Target | State | Major | Source | Action |
| --- | --- | --- | --- | --- |
| staging | missing-env | - | SUPABASE_STAGING_DB_URL | Set SUPABASE_STAGING_DB_URL locally or paste sanitized Supabase SQL Editor `select version();` output with --offline-version staging=... |
| production | missing-env | - | SUPABASE_PROD_DB_URL | Set SUPABASE_PROD_DB_URL locally or paste sanitized Supabase SQL Editor `select version();` output with --offline-version production=... |

## Pre-Upgrade Gate

- Record a fresh Supabase backup or PITR timestamp before changing Postgres major versions.
- Run the version check for both staging and production; production must not be upgraded first.
- Review extensions before upgrading, especially TimescaleDB, plv8, pg_graphql, pgjwt, and deprecated Postgres 17 extensions.
- Check logical replication slots and recreate them after upgrade if used.
- Reserve a maintenance window and announce write-impacting downtime before production upgrade.
- Run API smoke tests, RLS tests, migration validation, and the public demo guard after staging and production checks.

## Secret Policy

Database URLs and service role keys must stay in local env vars or GitHub Secrets. Reports contain only redacted URLs and sanitized version strings.
