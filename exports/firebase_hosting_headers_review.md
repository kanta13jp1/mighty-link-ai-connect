# Firebase Hosting Security Headers Review (T835)

- Generated at (UTC): 2026-06-23T15:48:06Z
- Firebase config: `firebase.json`
- Status: **PASS**
- Reviewed source rules: `**`

## Headers

| Header | Value |
| :--- | :--- |
| `content-security-policy` | `default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; media-src 'self' data: blob:; connect-src 'self' https://*.supabase.co https://*.googleapis.com https://firebaseinstallations.googleapis.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://firestore.googleapis.com https://storage.googleapis.com; worker-src 'self' blob:; frame-src 'self'; upgrade-insecure-requests` |
| `permissions-policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), clipboard-write=(self), fullscreen=(self)` |
| `referrer-policy` | `strict-origin-when-cross-origin` |
| `strict-transport-security` | `max-age=31536000` |
| `x-content-type-options` | `nosniff` |
| `x-frame-options` | `DENY` |

## Findings

- No blocking findings.

## Notes

- Firebase Hosting production URL is the public paid launch target.
- GitHub Pages is a static CEO demo mirror and cannot set arbitrary response headers from repository files.
- Current inline scripts/styles require unsafe-inline; migrate to CSP nonce/hash when the frontend bundle is refactored.
