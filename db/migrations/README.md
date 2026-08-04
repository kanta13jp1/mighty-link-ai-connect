# Database Migrations

`db/migrations/` contains application runtime schema migrations used by
`scripts/manage_db_migrations.py`.

- `sqlite/`: local fallback schema used by tests and local development.
- `postgres/`: Supabase/PostgreSQL runtime tables used by the FastAPI app.
- `supabase/migrations/`: Supabase product-domain schema, RLS policies, and
  database objects managed by the Supabase CLI.

Rules:

1. Create new files as `YYYYMMDDHHMMSS_short_slug.sql`.
2. Never edit a migration that has already been applied to a shared database.
   Add a forward-fix migration instead.
3. Validate migrations before merging:
   `python scripts/manage_db_migrations.py validate --engine sqlite`
4. Dry-run local application before applying:
   `python scripts/manage_db_migrations.py apply --engine sqlite --sqlite-path data/mighty.db --dry-run`
5. Apply to Supabase only after backup, staging validation, and one-lane
   deployment coordination.


- [Master Knowledge Graph Index](../../docs/MASTER_KNOWLEDGE_GRAPH.md)
