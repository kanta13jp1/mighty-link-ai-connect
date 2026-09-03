# Supabase UAT Credential Incident — 2026-08-30

## Status

- Incident: **REOPENED / CONTAINED / REMEDIATION IN PROGRESS** (`T999`, `T1005`, `R151`, `SEC-011`)
- Affected evidence: GitHub Actions run `33309776182` and Artifact `9731612926`
- Containment: both were deleted and independently confirmed as HTTP 404
- Data writes: the UAT connection failed before the rollback-only probe opened a database connection; no probe row was written
- Secret handling: no password, connection URL, or leaked fragment is recorded in this document
- Close decision: on 2026-08-31, the user explicitly decided that database-password rotation and `SUPABASE_DB_URL` replacement are not required at this time and accepted the residual risk
- Validation limit: PostgreSQL 17 and the 15/15 INSERT/readback/ROLLBACK check with `persisted_probe_records=0` have not been proven by a live green run; this closure is not a claim of technical remediation

## 2026-09-03 recurrence and containment

- Production Operations Monitor run `33694964498` failed at `sales-email-sync / Publish parsed records to Supabase` on default-branch SHA `280fff5a97c99dde89ad35d990ef828629428801`.
- The database driver emitted a credential-derived fragment after parsing an invalid URL. No secret value or fragment is retained in this document.
- The default-branch `sync_sqlite_to_supabase.py` had neither the UAT verifier's pre-connect URL validation nor its exception suppression.
- The workflow materialized `SALES_EMAIL_IMAP_ENV` into `.env`, and `load_env_file()` unconditionally overwrote the dedicated job-level `SUPABASE_DB_URL`. This allowed an older composite setting to take precedence over the intended repository secret.
- The run's nonsecret identity, SHA, job, failing step, timestamps, conclusion, and single uptime-report artifact name were preserved in Issue `#306`. The run was then deleted because its log contained credential-derived material; the GitHub Actions API returned `404` afterward.
- `T1005` adds canonical Supavisor URL validation before connecting, preserves explicit environment-variable precedence, suppresses all driver exception text behind one allowlisted message, exits nonzero on every failure, and adds focused regression tests. `sales-email-sync` remains fail-closed.
- Password rotation, repository secret replacement, Functions runtime redeployment, green monitor rerun, and live production verification remain required before `T999`, `R151`, and `SEC-011` can close.

## Cause

The GitHub Actions `SUPABASE_DB_URL` contained a reserved password character that was not percent-encoded. URI parsing treated part of the credential as a hostname, and the PostgreSQL driver included that parsed fragment in its DNS error. GitHub's full-secret mask cannot reliably redact substrings produced by a parser.

## Risk-acceptance boundary and reopen conditions

The incident is closed for tracking purposes under explicit user risk acceptance. The database password was not rotated, `SUPABASE_DB_URL` was not replaced, and the live 15/15 rollback-only UAT was not completed.

Reopen `T999`, `R151`, and `SEC-011` before any of the following:

1. Reusing or relying on the existing `SUPABASE_DB_URL` for a production write-verification run.
2. Treating Supabase write/readback compatibility as a release or production-readiness proof.
3. Observing another connection, parsing, authentication, or redaction failure.
4. Removing or weakening any of the URL validation, exception suppression, transaction rollback, or fail-closed controls.

At reopen, reset the database password, copy the current Dashboard-provided Supavisor URI, percent-encode reserved password characters, replace the GitHub Actions secret, and run the rollback-only verification. Do not paste credentials into chat, Issues, docs, terminal arguments, or workflow logs.

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
