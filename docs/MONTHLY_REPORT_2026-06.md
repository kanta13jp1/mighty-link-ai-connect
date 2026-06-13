# Mighty Skill-Bridge 月次品質レポート: 2026年06月

> [!NOTE]
> 月中時点の中間スナップショットです（生成日: 2026-06-13）。確定版は翌月 1 日に再生成します（T767 スケジュール）。

**作成日**: 2026-06-13
**作成者**: 梅澤 寛太（+ Claude Code, scripts/generate_monthly_quality_report.py による自動生成）

---

## 1. WBS 進捗

| 指標 | 今月 | 先月比 |
| :--- | :--- | :--- |
| 当月完了タスク数 | 79 件 | -20 件 |
| 全体完了率 | 79.1% (178/225) | — |
| 期限超過の未完了タスク | 0 件 | — |

---

## 2. サービス品質 KPI

| KPI | 今月実績 | 目標 | 判定 |
| :--- | :--- | :--- | :--- |
| テスト合格率 | 100.0% (33/33) | 100% | ✅ |
| AI 診断 API 課金実行件数 | 0 件 | コストガード内 | ✅ |
| 稼働率 / P95 / 5xx エラー率 | 未計測 | ≥99.5% / ≤3.0s / ≤0.5% | ⏳ 計測基盤整備中（T743 死活監視・T755 テレメトリ・T778 SLA ビュー） |

---

## 3. 外部 API 利用・コスト

日次利用台帳監査（`reports/daily_usage_audit_*.json`、当月 1 日分）の集計:

| プロバイダ:操作 | 課金実行 | ガード遮断 | 報告トークン |
| :--- | ---: | ---: | ---: |
| gemini_api:match | 0 | 0 | 0 |
| gemini_api:parse | 0 | 0 | 0 |
| seedance_api:generation_create | 0 | 8 | 0 |

ガードアラート: 0 件（コストガードはすべて上限内）

金額ベースの実測は [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md) を参照（GCP Billing API 連携は T757 週次コストダッシュボードで自動化予定）。

---

## 4. インシデント・課題（当月起票/更新）

| ID | 重要度 | 状態 | タイトル |
| :--- | :--- | :--- | :--- |
| R10 | MED | resolved | 公開 URL の外部漏洩 (方向性 A/C 選択時) |
| HANDOFF-4 | MED | resolved | scripts/sync_docs_to_notebooklm.py に Gemini explicit context caching 導入 |
| HANDOFF-5 | LOW | resolved | Codex skills packaging (/sync-wbs, /sync-notebooklm, /verify-demo) |
| HANDOFF-15 | LOW | resolved | scripts/generate_ceo_presentation_deck.py に --style canva-export オプション追加 |
| HANDOFF-25 | LOW | resolved | Figma wireframe ファイルへの MCP 流し込み (rate limit 解除待ち) |
| R28 | HIGH | open | 経歴書のマスキング法務合意確認 |
| R29 | MED | resolved | APIコストの月額制限の検証 |
| R30 | LOW | open | 録画データの整理 |
| R31 | MED | open | 既存診断ツールの選定調査 |
| R32 | HIGH | open | AI適性状況診断ツールの実装 |
| R33 | HIGH | open | 勤務表データの自動解析実装 |
| R34 | MED | open | 開発マイルストーンの策定 |
| R35 | MED | open | APIコストの月額制限の検証 |
| R36 | HIGH | open | 経歴書と心理データの法務合意確認 |
| R37 | HIGH | open | Firebase ホスティング デプロイの認証情報およびターゲット設定エラー |
| R38 | MED | resolved | Firebase main/master 同時デプロイ競合による Cloud Functions 更新失敗 |
| R39 | HIGH | resolved | Firebase Functions invoker IAM 権限不足による CI 失敗 |
| R40 | MED | resolved | WBS タスクID重複（T774/T775 二重定義）による誤完了フラグ |
| R41 | HIGH | resolved | 認証なし DB 診断エンドポイント /api/db-test の露出 |
| R42 | MED | resolved | GitHub Actions Node 20 action runtime deprecation warnings |
| R43 | MED | resolved | GitHub Project item追加 API が 401 を返す |
| R45 | HIGH | resolved | Firebase/Supabase staging と production の接続情報混在リスク |
| R44 | HIGH | resolved | 本番 /api/* 全エンドポイント 502/504（Cloud Functions 全リクエストハング） |
| R46 | MED | resolved | 比較ボード「詳細分析」がスキルカテゴリ名と定型文を /api/match へ送信し無意味な診断を生成 |
| R47 | LOW | resolved | deterministic fallback の QA 質問テンプレートにプレースホルダ文が混入 |
| R48 | HIGH | open | 利用規約・プライバシーポリシー初版の法務確認待ち |
| R49 | HIGH | resolved | starlette 0.52.1 に CVE-2026-48710（Host ヘッダ未検証による request.url パス乖離） |
| R50 | MED | resolved | Google API 呼び出し 17 箇所で requests timeout 未指定（bandit B113） |
| R51 | MED | open | 特商法表記の事業者情報・販売価格の確定待ち |
| R52 | LOW | resolved | FastAPI @app.on_event("startup") が deprecated（lifespan ハンドラへ移行要） |
| R53 | MED | open | Supabase Postgres 14 サポート終了 (2026-07-01) — 本番/staging プロジェクトの PG バージョン未確認 |
| R54 | HIGH | resolved | ml-mightylink.com の Cloud DNS ゾーン所有アカウント不明 — T740 カスタムドメイン CNAME 追加がブロック |

**セキュリティ検出（security_log）:**

- SEC-004 [HIGH] bandit B324: Calendar syncKey 生成に SHA1 を使用（弱ハッシュ警告） — FIXED
- SEC-005 [HIGH] pip-audit: CVE-2026-48710 Host ヘッダ未検証による request.url パス乖離（パス認可バイパスの可能性） — FIXED
- SEC-006 [MED] bandit B113: requests timeout 未指定 17 箇所（sync スクリプト無期限ハングリスク） — FIXED
- SEC-007 [LOW] bandit B310 urlopen scheme / B108 hardcoded /tmp — FIXED

---

## 5. 翌月（または直近）の優先アクション

1. T781 サービス終了（EOL）やデータ移行に備えたユーザーデータのセルフエクスポート機能の設計とPoC（開始 2026-07-01 / 担当 Codex）
2. T791 Stripe Billing Meters API を用いた課金実装・Webhook 検証・本番適用（開始 2026-07-01 / 担当 Codex）
3. T782 アクセス増加に伴うデータベース接続負荷分散（リードレプリカ・プールサイズ最適化）の設計と負荷テスト検証（開始 2026-07-02 / 担当 Codex）
4. T805 外部ペネトレーションテスト（第三者脆弱性診断）の計画・実施（開始 2026-07-02 / 担当 人間 + Codex）
5. T807 サブスクリプション解約・プラン変更フロー（Stripe カスタマーポータル）の実装（開始 2026-07-03 / 担当 Codex）

---

## 6. 参照リンク

- [WBS スプレッドシート](https://docs.google.com/spreadsheets/d/1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8)
- [GitHub リポジトリ](https://github.com/kanta13jp1/mighty-link-ai-connect)
- [公開デモ URL](https://kanta13jp1.github.io/mighty-link-ai-connect/)
- [SLA/KPI 定義](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) / [レポート仕様 (T767)](MONTHLY_PROGRESS_REPORT_AND_KPI_DASHBOARD.md)
