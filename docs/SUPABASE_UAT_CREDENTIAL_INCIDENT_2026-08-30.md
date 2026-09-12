# Supabase UAT Credential Incident — 2026-08-30

## Status

- Incident: **RESOLVED / TECHNICALLY REMEDIATED** (`T999`, `T1005`, `R151`, `SEC-011`)
- Affected evidence: GitHub Actions runs `33309776182` and `33694964498`; both were deleted after preserving nonsecret metadata and independently confirmed as HTTP 404
- Code remediation: exact SHA `760996b0d9793fe258b85eac5ee04f6c9859e687`; Cloud Full Preflight run `33700548449` passed
- Credential remediation: database password rotated and repository `SUPABASE_DB_URL` replaced on `2026-09-03T00:45:25Z`
- Operations validation: Production Operations Monitor run `33701468205` passed both uptime and `sales-email-sync`
- Database validation: Supabase Production UAT run `33701556025` passed 15/15 INSERT/readback checks, rolled back, and persisted 0 probe records on PostgreSQL 17
- Runtime validation: manual CI/CD run `33701689340` deployed Functions/Hosting with the rotated setting; the authenticated live guard for `https://mightylink-app.com/` passed afterward
- Secret handling: no password, connection URL, or leaked fragment is recorded in this document

## 2026-09-03 recurrence and containment

- Production Operations Monitor run `33694964498` failed at `sales-email-sync / Publish parsed records to Supabase` on default-branch SHA `280fff5a97c99dde89ad35d990ef828629428801`.
- The database driver emitted a credential-derived fragment after parsing an invalid URL. No secret value or fragment is retained in this document.
- The default-branch `sync_sqlite_to_supabase.py` had neither the UAT verifier's pre-connect URL validation nor its exception suppression.
- The workflow materialized `SALES_EMAIL_IMAP_ENV` into `.env`, and `load_env_file()` unconditionally overwrote the dedicated job-level `SUPABASE_DB_URL`. This allowed an older composite setting to take precedence over the intended repository secret.
- The run's nonsecret identity, SHA, job, failing step, timestamps, conclusion, and single uptime-report artifact name were preserved in Issue `#306`. The run was then deleted because its log contained credential-derived material; the GitHub Actions API returned `404` afterward.
- `T1005` adds canonical Supavisor URL validation before connecting, preserves explicit environment-variable precedence, suppresses all driver exception text behind one allowlisted message, exits nonzero on every failure, and adds focused regression tests. `sales-email-sync` remains fail-closed.
- Password rotation, repository secret replacement, Functions runtime deployment, green monitor rerun, rollback-only live UAT, and authenticated production verification completed on 2026-09-03. `T999`, `R151`, and `SEC-011` may close.

## Cause

The GitHub Actions `SUPABASE_DB_URL` contained a reserved password character that was not percent-encoded. URI parsing treated part of the credential as a hostname, and the PostgreSQL driver included that parsed fragment in its DNS error. GitHub's full-secret mask cannot reliably redact substrings produced by a parser.

## Closure boundary and reopen conditions

This incident is technically remediated, rather than closed through residual-risk acceptance. Reopen `T999`, `R151`, and `SEC-011` if a connection, parsing, authentication, or redaction failure recurs, or if any URL-validation, exception-suppression, transaction-rollback, or fail-closed control is weakened.

For any future rotation, reset the database password, copy the current Dashboard-provided Supavisor URI, percent-encode reserved password characters, replace the GitHub Actions secret, deploy the Functions runtime setting, and rerun both the monitor and rollback-only UAT. Do not paste credentials into chat, Issues, docs, terminal arguments, or workflow logs.

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
