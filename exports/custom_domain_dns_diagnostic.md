# Custom Domain DNS Diagnostic

- Generated: 2026-06-27T12:33:20Z
- Domain: `mightylink-app.com`
- Status: `blocked`
- Blockers: rdap_client_hold, public_dns_nxdomain

## RDAP

- Statuses: client hold
- Nameservers: 01.DNSV.JP, 02.DNSV.JP, 03.DNSV.JP, 04.DNSV.JP

## RDAP Events

- registration: 2026-06-13T02:26:53Z
- expiration: 2027-06-13T02:26:53Z
- last changed: 2026-06-27T02:30:28Z
- last update of RDAP database: 2026-06-27T12:33:03Z

## DNS Summary

- 8.8.8.8 NS: NXDOMAIN
- 8.8.8.8 SOA: NXDOMAIN
- 8.8.8.8 A: NXDOMAIN
- 8.8.8.8 AAAA: NXDOMAIN
- 8.8.8.8 TXT: NXDOMAIN
- 1.1.1.1 NS: NXDOMAIN
- 1.1.1.1 SOA: NXDOMAIN
- 1.1.1.1 A: NXDOMAIN
- 1.1.1.1 AAAA: NXDOMAIN
- 1.1.1.1 TXT: NXDOMAIN

## Recommendations

- Ask the onamae.com domain owner to confirm why the domain is on client hold and complete any required verification, payment, abuse, or registrant-data action.
- Verify authoritative DNS delegation and publish the Firebase Hosting required records on the DNS zone that is actually authoritative after the hold is cleared.
- Compare the RDAP nameservers with the DNS provider where records are being edited.

## Official Docs

- Firebase Hosting custom domain: https://firebase.google.com/docs/hosting/custom-domain
- onamae.com DNS record setup: https://help.onamae.com/answer/14353
- ICANN EPP status codes: https://icann.org/epp
