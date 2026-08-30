# Weekly Security Scan修復記録（2026-08-30 / T998）

## エグゼクティブサマリー

PR #303のWeekly Security Scanで検出された依存脆弱性5件とBandit Medium 29件を修復した。認証、TLS検証、sales-email-syncのfail-closed動作、RLS、シークレット要件は緩和していない。候補SHA `4d937ffe4dfdd36f9436f36598cee9d98d143df2` でBandit High/Medium 0件、pip-audit 0件、full preflight、CI/CDおよび関連運用ワークフローの成功を確認した。

## 検出事項と対応

### SEC-009 — Starlette既知脆弱性

- 重要度: High
- 場所: `requirements.txt:3-7`
- 証跡: Starlette 1.0.1に対してpip-auditが修正版1.1.0、1.3.0、1.3.1を示す既知脆弱性5件を検出した。
- 影響: Host/リクエスト処理、multipart、Range処理などASGI境界の既知欠陥が残る可能性。
- 修正: FastAPI `>=0.141.1,<0.142.0`、Starlette `>=1.6.0,<1.7.0`、python-multipart `>=0.0.18`へ更新した。
- 検証: Actions `33308264395` でpip-audit 0件。

### SEC-010 — 外向き通信・動的SQL・XML解析

- 重要度: Medium
- 場所:
  - `scripts/network_security.py:20-55`
  - `scripts/parse_sales_emails.py:32-41`
  - `scripts/run_lane_preflight.py:32,221`
  - `src/app.py:3525-3655`
- 証跡: Bandit B310/B323/B608/B314 合計29件。
- 影響: 未検証URLによるSSRF/危険スキーム、動的識別子の将来的なSQL注入、悪意あるXMLによるリソース枯渇の可能性。
- 修正:
  - 外向きURLをHTTPS、固定ホスト、または明示的ループバックへ制限。
  - SQL値のパラメータ化を維持し、ビュー・テーブル・列識別子を固定許可集合へ制限。
  - JUnit XML解析を`defusedxml.ElementTree`へ変更。
  - TLS未検証fallbackは証明書障害の診断専用とし、結果を必ずwarningとして扱う既存契約を維持。該当B323だけを行単位で限定抑制。
- 検証: Actions `33308264395` でBandit High/Medium 0件。全体除外、設定緩和、スキャン無効化は行っていない。

## 回帰テスト

- `tests/test_security_scan_remediation.py`
  - リモートHTTP、資格情報埋め込みURL、LAN宛てHTTPを拒否。
  - HTTPSと明示的loopbackのみ許可。
  - 修正版依存範囲とArtifact保存契約を固定。
  - 不正なSQL列名と未知SLAビューを実行前に拒否。
- `sales-email-sync`のsecret必須、受信0件失敗、Supabase publish失敗時のfail-closedテストは変更・緩和していない。

## クラウド検証証跡

| 検証 | Actions run | 結果 |
| --- | ---: | --- |
| Weekly Security Scan | 33308264395 | PASS |
| Cloud Full Preflight（push exact SHA） | 33308260188 | PASS |
| Cloud Full Preflight（PR exact SHA） | 33308264393 | PASS |
| CI/CD Pipeline | 33308264568 | PASS |
| Public Demo Guard | 33308264551 | PASS |
| Infra Telemetry Dashboard | 33308264429 | PASS |
| Quota Error Alert Review | 33308264390 | PASS |
| Weekly Cost Dashboard | 33308264384 | PASS |
| Monthly Quality Report Delivery | 33308264521 | PASS |

Weekly Security Scanは`bandit_weekly.txt`と`pip_audit_weekly.json`を成功・失敗にかかわらず14日間Artifactとして保存する。

## 残余リスク

この修復範囲に未解決のHigh/Medium検出はない。今後、許可済みURLホストやSQLスキーマを拡張する場合は、同じ許可集合と回帰テストを同時更新する。