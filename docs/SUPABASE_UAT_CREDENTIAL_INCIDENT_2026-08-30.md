# Supabase UAT Credential Incident — 2026-08-30

## Status

- Incident: **OPEN / MITIGATING** (`T999`, `R151`, `SEC-011`)
- Affected evidence: GitHub Actions run `33309776182` and Artifact `9731612926`
- Containment: both were deleted and independently confirmed as HTTP 404
- Data writes: the UAT connection failed before the rollback-only probe opened a database connection; no probe row was written
- Secret handling: no password, connection URL, or leaked fragment is recorded in this document

## Cause

The GitHub Actions `SUPABASE_DB_URL` contained a reserved password character that was not percent-encoded. URI parsing treated part of the credential as a hostname, and the PostgreSQL driver included that parsed fragment in its DNS error. GitHub's full-secret mask cannot reliably redact substrings produced by a parser.

## Required recovery order

1. In Supabase Dashboard, open **Database > Settings** and reset the project database password. Do not paste the password into chat, Issues, docs, terminal arguments, or workflow logs.
2. From Supabase Dashboard **Connect**, copy the current Supavisor connection string. Percent-encode every reserved password character. Use the Dashboard-provided pooler host/user/port and require TLS (`sslmode=require`).
3. In GitHub repository **Settings > Secrets and variables > Actions**, replace `SUPABASE_DB_URL`. Store only the full encoded connection URL as the secret; never commit it.
4. Run `Supabase Production UAT Write Verification` from `main` after the T999 logging fix is deployed.
5. Close T999/R151/SEC-011 only when the new run proves PostgreSQL 17, all 15 table probes PASS, ROLLBACK succeeds, and `persisted_probe_records=0`.

## Code-side prevention

- Validate scheme, Supabase host, username shape, port, database path, allowed query, percent escapes, and raw reserved characters before calling the database driver.
- Fail closed for an absent or invalid secret.
- Suppress all third-party exception text in console and Artifact output; emit only an allowlisted failure code.
- Keep synthetic writes in one transaction and never call `commit()`.
- Do not weaken `sales-email-sync` fail-closed behavior.

## Official references

- Supabase, Reset database password: https://supabase.com/docs/guides/troubleshooting/how-do-i-reset-my-supabase-database-password-oTs5sB
- Supabase, Connect to Postgres: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase, Postgres roles and percent-encoding special password symbols: https://supabase.com/docs/guides/database/postgres/roles
