# mightylink-app.com DNS/HTTPS Uptime Incident

- Date: 2026-06-27
- Related WBS: T855
- Related issue: R103, GitHub Issue #143
- Related Go/No-Go: PUBLIC-16
- Scope: `public_paid_launch`, sales URL operation, uptime monitoring

---

## Summary

T854 closeout uncovered a new uptime regression for the sales custom domain.

`scripts/check_uptime_targets.py` and the scheduled GitHub Actions Public Uptime Monitor both show:

- `https://kanta13jp1.github.io/mighty-link-ai-connect/`: OK
- `https://mighty-link-ai-connect-13d22.web.app/`: OK
- `https://mightylink-app.com/`: Failed

The custom domain failure is DNS resolution failure:

```text
URLError: <urlopen error [Errno 11001] getaddrinfo failed>
```

This does not invalidate the CEO-shared GitHub Pages controlled demo, but it blocks the sales URL, `public_paid_launch`, and the final site development completion declaration.

---

## Decision

Add T855 as a required WBS task:

> Restore `mightylink-app.com` DNS/HTTPS uptime monitoring and re-check onamae.com / Firebase Hosting records.

Add PUBLIC-16 as a Go/No-Go blocker:

> The sales URL `https://mightylink-app.com/` must resolve and pass strict HTTPS uptime monitoring.

Keep T854 completed because the issue/QA blocker audit itself is complete. R103 is not left as an unclassified open tracker row; it is transferred to T855, GitHub Issue #143, and PUBLIC-16.

---

## Evidence

- GitHub Actions Public Uptime Monitor run: `28287944062`
- Local command: `python scripts/check_uptime_targets.py`
- Local report: `exports/uptime_monitor_report.json`
- Failed target: `UPTIME_CUSTOM_DOMAIN`
- Error: `getaddrinfo failed`

---

## Recovery Checklist

1. Open the onamae.com domain/DNS management screen for `mightylink-app.com`.
2. Confirm which provider currently controls the authoritative name servers.
3. Open the Firebase Hosting custom domain settings for `mightylink-app.com`.
4. Confirm the required TXT/A/AAAA/CNAME records shown by Firebase.
5. Remove or correct conflicting DNS records.
6. Confirm that CAA records do not block Google Trust Services certificate issuance.
7. Wait for DNS propagation where needed.
8. Run:

```powershell
python scripts/check_uptime_targets.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

9. Re-run or wait for the GitHub Actions Public Uptime Monitor and confirm green.
10. Update T855, R103, QA-83, PUBLIC-16, Sheets, Calendar, GitHub Issue #143, and GitHub Project #1.

---

## Official Docs Checked

- Firebase Hosting custom domain setup: https://firebase.google.com/docs/hosting/custom-domain
- onamae.com DNS record setup: https://help.onamae.com/answer/14353
