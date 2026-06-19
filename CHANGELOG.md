# Changelog

All notable changes to Mighty-Link AI Connect are tracked here.

This project follows Semantic Versioning for tags and release names. While the
service is still before general availability, release tags use prerelease
identifiers such as `controlled-demo`.

## [0.1.0-controlled-demo.1] - 2026-06-19

### Added

- Firebase Hosting custom domain baseline for `https://mightylink-app.com/`
  with Firebase-managed HTTPS certificate confirmed.
- Sales-email AI matching MVP foundations through T817_6: safe local intake,
  Supabase/RLS schema, deterministic extraction fallback, bidirectional
  matching API/UI, and human review feedback logging.
- Company account migration preparation runbook for GitHub, Firebase/GCP,
  Supabase, Google Workspace, NotebookLM, AI development tools, Stripe, and
  domain ownership.
- Release governance assets: production Go/No-Go checklist, rollback runbook,
  support escalation, monitoring, quota/cost reviews, and incident postmortem
  flow.

### Changed

- WBS, issue tracker, QA tracker, release decision, test results, NotebookLM,
  Google Sheets, Google Calendar, GitHub Issues, and GitHub Project are treated
  as closeout synchronization surfaces.
- Release scope is explicitly split between `controlled_demo` and
  `public_paid_launch`.

### Security

- Public artifacts and generated reports are kept secret-free. Gmail/OAuth,
  Supabase, Firebase/GCP, Slack, Stripe, and GitHub secrets must stay in local
  credentials, GitHub secrets, or provider consoles only.

### Release Boundary

- `controlled_demo`: GO for CEO/shared internal demonstration.
- `public_paid_launch`: NO_GO until legal approval, pricing approval, Stripe
  billing, onboarding, load testing, and T817_7 production hardening are
  complete.
