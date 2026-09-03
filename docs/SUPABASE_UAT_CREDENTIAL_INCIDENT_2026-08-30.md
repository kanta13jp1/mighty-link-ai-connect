# Supabase UAT Credential Incident — 2026-08-30

## Status

- Incident: **OPEN / RECURRENCE CONFIRMED** (`T999`, `R151`, `SEC-011`, Issue `#306`)
- Affected evidence: GitHub Actions run `33309776182` and Artifact `9731612926`
- Containment: both were deleted and independently confirmed as HTTP 404
- Data writes: the UAT connection failed before the rollback-only probe opened a database connection; no probe row was written
- Secret handling: no password, connection URL, or leaked fragment is recorded in this document
- Reopened: on 2026-09-03, Production Operations Monitor run `33694964498` reused the malformed secret in `sales-email-sync`; the database publish failed and a credential-derived fragment appeared in the driver error
- Code containment: `T1004` adds the same pre-connect URL validation and exception-text suppression to `scripts/sync_sqlite_to_supabase.py`
- Human action pending: rotate the database password, replace every copy of `SUPABASE_DB_URL`, decide disposal of the affected run after evidence preservation, and complete the rollback-only live verification
- Validation limit: PostgreSQL 17 and the 15/15 INSERT/readback/ROLLBACK check with `persisted_probe_records=0` have not been proven by a live green run; code containment is not a claim of credential remediation

## Cause

The GitHub Actions `SUPABASE_DB_URL` contained a reserved password character that was not percent-encoded. URI parsing treated part of the credential as a hostname, and the PostgreSQL driver included that parsed fragment in its DNS error. GitHub's full-secret mask cannot reliably redact substrings produced by a parser.

## Risk-acceptance boundary and reopen conditions

The earlier risk-accepted closure ended when the malformed secret was reused on 2026-09-03. The database password has not been rotated, `SUPABASE_DB_URL` has not been replaced, and the live 15/15 rollback-only UAT has not been completed, so the incident remains open.

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
- Apply the same URL validator before every sales-email Supabase publish and suppress exception values at the CLI boundary (`T1004`).

## Official references

- Supabase, Reset database password: https://supabase.com/docs/guides/troubleshooting/how-do-i-reset-my-supabase-database-password-oTs5sB
- Supabase, Connect to Postgres: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase, Postgres roles and percent-encoding special password symbols: https://supabase.com/docs/guides/database/postgres/roles
