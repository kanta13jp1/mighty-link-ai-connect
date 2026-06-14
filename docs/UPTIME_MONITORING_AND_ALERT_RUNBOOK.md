# 本番死活監視・Slackアラート Runbook (T743)

作成日: 2026-06-14
担当レーン: VSCode + Codex
対象: GitHub Pages / Firebase Hosting / mightylink-app.com

## 目的

本番公開URLの到達性を定期確認し、停止やHTTP異常を GitHub Actions と Slack 通知で早期検知する。T740_3 完了により `mightylink-app.com` は Google Trust Services 証明書の Subject が `CN=mightylink-app.com` と一致したため、strict TLS 監視を正とする。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- Firebase Hosting custom domain: カスタムドメインはDNS検証後にSSL証明書が自動プロビジョニングされる。
- Firebase Functions environment configuration: secrets は環境変数やSecret Managerで扱い、コードやreportへ保存しない。
- GitHub Actions secrets: workflow では secrets コンテキストを使い、ログや成果物へ値を出さない。
- Slack developer docs: Incoming webhook は通知専用のsecretとして扱い、失敗時の要約だけを送る。
- OpenAI Codex / Anthropic Claude Code: agent作業はWBS・Issue・検証ログへ接続し、外部toolの権限と証跡を明示する。

## 監視構成

| ファイル | 役割 |
| --- | --- |
| `data/uptime_targets.tsv` | 監視対象URL、期待HTTPステータス、TLS例外可否、severity、ownerの正本 |
| `scripts/check_uptime_targets.py` | TSVを読み、各URLをGETしてJSON reportを生成する |
| `.github/workflows/uptime-monitor.yml` | 30分間隔または手動で死活監視を実行する |
| `exports/uptime_monitor_report.json` | 直近実行結果。失敗・warning・レイテンシを記録する |

## 手動実行

```powershell
python scripts/check_uptime_targets.py
```

失敗時にSlack通知も送る場合:

```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
python scripts/check_uptime_targets.py --notify-on-failure
```

## 判定ルール

| 状態 | 意味 | exit code |
| --- | --- | --- |
| `ok` | strict TLSで期待HTTPステータスを返した | 0 |
| `warning` | `allow_tls_error=true` の対象でstrict TLSは失敗したが、到達性は確認できた | 0 |
| `failed` | HTTP異常、DNS失敗、timeout、または許可されないTLS失敗 | 1 |

`mightylink-app.com` はT740_3完了済みのため `allow_tls_error=false` にする。証明書ホスト名不一致が再発した場合は warning ではなく failed として扱う。

## 障害時の初動

1. GitHub Actions の `Public Uptime Monitor` run と `exports/uptime_monitor_report.json` を確認する。
2. 失敗URLが GitHub Pages か Firebase Hosting か custom domain かを切り分ける。
3. Firebase Hosting のrelease履歴、GitHub Pagesの公開状態、DNS A/TXT、SSL証明書SANを確認する。
4. P1/P2相当なら [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) に従って連絡する。
5. 復旧後24時間以内に [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) に従ってポストモーテムを残す。

## Slack通知

GitHub repository secret `SLACK_WEBHOOK_URL` が設定されている場合、失敗時に以下を通知する。

- 総件数、ok/warning/failed件数
- 失敗またはwarningのtarget_id、URL、error

secretが未設定の場合もworkflowは監視として機能し、失敗はGitHub Actionsの赤runとして検知する。

## 関連ドキュメント

- [PRODUCTION_DOMAIN_SETUP_GUIDE.md](PRODUCTION_DOMAIN_SETUP_GUIDE.md)
- [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md)
- [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md)
- [WBS.md](WBS.md)
