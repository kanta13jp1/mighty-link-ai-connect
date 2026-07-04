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

## T856 Diagnostic Result

T856 added `scripts/diagnose_custom_domain_dns.py` and generated:

- `exports/custom_domain_dns_diagnostic.json`
- `exports/custom_domain_dns_diagnostic.md`

The diagnostic result is:

- RDAP status: `client hold`
- RDAP registrar: GMO Internet Group / onamae.com
- RDAP nameservers: `01.DNSV.JP`, `02.DNSV.JP`, `03.DNSV.JP`, `04.DNSV.JP`
- Google Public DNS `8.8.8.8`: `NS` / `SOA` / `A` / `AAAA` / `TXT` all NXDOMAIN
- Cloudflare Public DNS `1.1.1.1`: `NS` / `SOA` / `A` / `AAAA` / `TXT` all NXDOMAIN

This points first to a registrar-side hold/delegation problem, not merely a missing Firebase `A` record. T855 remains open because解除 of `client hold` and DNS record changes require authenticated onamae.com / domain-owner action. Do not write registrar credentials, DNS control-panel screenshots containing secrets, or account recovery details into GitHub, Sheets, docs, or NotebookLM.

---

## 2026-07-04 Re-diagnosis: Root Cause Confirmed

`python scripts/diagnose_custom_domain_dns.py`（2026-07-04T04:05Z）の結果:

- RDAP status: `client hold`（継続中）
- expiration: **2027-06-13**（期限切れではない。1年分登録済み）
- registration: 2026-06-13 / RDAP last changed: **2026-06-27T02:30Z**
- 8.8.8.8 / 1.1.1.1 とも全レコード NXDOMAIN（client hold により .com ゾーンから委任が外されているため）

**確定原因: お名前.com のドメイン情報認証（ICANN 登録者メールアドレス有効性確認）が未完了のまま期限を超過し、レジストラが clientHold を適用した。**

根拠: お名前.com 公式ヘルプ（answer/15333）のとおり、新規取得後に登録者メールアドレスへ届く「【重要】[お名前.com] ドメイン情報認証のお願い」の URL へ **2週間（336時間）以内** にアクセスしないと clientHold になる。本ドメインは 6/13 登録 → 6/27 に status 変更で、ちょうど14日後に一致する。料金未納や abuse ではない。

### 解除手順（ドメイン所有者の作業）

1. ドメイン登録時に使ったメールアドレスの受信箱（迷惑メールフォルダ含む）で「【重要】[お名前.com] ドメイン情報認証のお願い」を探し、本文中の認証 URL へアクセスする。
2. メールが見つからない場合は、お名前.com Navi にログインし、ドメイン情報認証の再送（または WHOIS 登録者メールアドレスの修正 → 認証メール再送）を行う。
3. 認証完了後、clientHold は早ければ30分〜数時間で解除され、`01.DNSV.JP`〜`04.DNSV.JP` への委任が復活する。
4. 解除後に Firebase Hosting custom domain の要求レコード（A/AAAA/TXT/CAA）がお名前.com の DNS ゾーンに揃っているかを確認する（下記チェックリスト 4〜8）。
5. `python scripts/diagnose_custom_domain_dns.py` と `python scripts/check_uptime_targets.py` で green を確認し、T855/PUBLIC-16/Issue #143 を更新する。

認証 URL、お名前.com の認証情報、Navi のスクリーンショットは GitHub、Sheets、docs、NotebookLM へ記録しない。

## Recovery Checklist

1. Open the onamae.com domain/DNS management screen for `mightylink-app.com`.
2. Confirm why RDAP shows `client hold`; complete any registrar-required identity, payment, registrant information, or policy-clearance action.
3. Confirm which provider currently controls the authoritative name servers. RDAP currently lists `01.DNSV.JP` to `04.DNSV.JP`.
4. Open the Firebase Hosting custom domain settings for `mightylink-app.com`.
5. Confirm the required TXT/A/AAAA/CNAME records shown by Firebase.
6. Remove or correct conflicting DNS records.
7. Confirm that CAA records do not block Google Trust Services certificate issuance.
8. Wait for registrar status and DNS propagation where needed.
9. Run:

```powershell
python scripts/diagnose_custom_domain_dns.py
python scripts/check_uptime_targets.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

10. Re-run or wait for the GitHub Actions Public Uptime Monitor and confirm green.
11. Update T855, R103, QA-83, PUBLIC-16, Sheets, Calendar, GitHub Issue #143, and GitHub Project #1.

---

## Official Docs Checked

- Firebase Hosting custom domain setup: https://firebase.google.com/docs/hosting/custom-domain
- onamae.com DNS record setup: https://help.onamae.com/answer/14353
