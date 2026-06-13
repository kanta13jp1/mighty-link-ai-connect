# サービス品質KPI・SLA定義と計測基盤整備 (T762)

**Mighty Skill-Bridge** 本番サービスの品質目標（KPI）とサービスレベル合意（SLA）を定義し、継続的に計測・報告するための基盤を整備します。

---

## バージョン履歴

| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-10 | v1.0.0 | 初版作成（KPI/SLA定義・Supabaseビュー・月次レポート仕様） | Claude Code |

---

## 1. SLA 定義

### 1.1 稼働率（Availability）

| ティア | 目標値 | 月間許容ダウンタイム | 対象期間 |
| :--- | :--- | :--- | :--- |
| 本番（パイロット期） | **99.5%** | 約 3.6 時間/月 | 2026-06〜2026-09 |
| 本番（一般公開後） | **99.9%** | 約 43 分/月 | 2026-10〜 |

計測方法：Google Cloud Monitoring の Uptime Check（1分間隔）で `https://<本番URL>/api/v1/health` を監視。

### 1.2 API レスポンスタイム（Latency）

| パーセンタイル | 目標値 | 対象エンドポイント |
| :--- | :--- | :--- |
| P50 (中央値) | ≤ 1.5 秒 | 全エンドポイント |
| P95 | ≤ 3.0 秒 | 全エンドポイント |
| P99 | ≤ 8.0 秒 | AI診断エンドポイント（`/api/v1/diagnose`） |

### 1.3 エラー率

| 指標 | 目標値 |
| :--- | :--- |
| HTTP 5xx エラー率 | ≤ 0.5% |
| AI診断 タイムアウト率 | ≤ 2.0% |

---

## 2. KPI 定義

### 2.1 ビジネス KPI

| KPI | 定義 | 計測頻度 | 目標（パイロット期） |
| :--- | :--- | :--- | :--- |
| 診断実行件数 | `matches` テーブルの INSERT 件数 | 日次 | ≥ 5 件/週 |
| 診断精度スコア | ユーザーが「役に立った」を選択した割合 | 週次 | ≥ 70% |
| アクティブユーザー数 | 過去7日間にログインした `profiles` 件数 | 週次 | ≥ 3 名 |
| オンボーディング完了率 | 登録→初回診断完了までの割合 | 月次 | ≥ 80% |

### 2.2 インフラ KPI

| KPI | 定義 | 計測頻度 | 目標 |
| :--- | :--- | :--- | :--- |
| Gemini API コスト | 月間 Gemini API 費用（USD） | 月次 | ≤ $50/月 |
| Firebase 月間コスト | Hosting + Functions + Auth 合計 | 月次 | ≤ $30/月 |
| Supabase DB 使用量 | DB サイズ（MB） | 月次 | ≤ 500 MB（Free tier上限） |
| Cloud Functions 実行時間 | 月間累計実行時間（ms） | 月次 | ≤ 400,000 ms（無料枠内） |

---

## 3. Supabase ビュー設計（計測基盤）

### 3.1 日次診断件数ビュー

```sql
CREATE OR REPLACE VIEW public.kpi_daily_diagnoses AS
SELECT
  DATE_TRUNC('day', created_at AT TIME ZONE 'Asia/Tokyo') AS diagnosis_date,
  COUNT(*) AS diagnosis_count,
  COUNT(DISTINCT user_id) AS unique_users,
  AVG(fit_score) AS avg_fit_score,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fit_score) AS median_fit_score
FROM public.matches
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1 DESC;
```

### 3.2 週次アクティブユーザービュー

```sql
CREATE OR REPLACE VIEW public.kpi_weekly_active_users AS
SELECT
  DATE_TRUNC('week', last_login AT TIME ZONE 'Asia/Tokyo') AS week_start,
  COUNT(DISTINCT user_id) AS wau
FROM public.profiles
WHERE last_login >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1 DESC;
```

### 3.3 SLA 稼働率計算ビュー（Uptime チェック結果を Supabase に保存する場合）

```sql
-- uptime_checks テーブルが存在する前提
CREATE OR REPLACE VIEW public.kpi_monthly_availability AS
SELECT
  DATE_TRUNC('month', checked_at) AS month,
  COUNT(*) AS total_checks,
  SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS up_checks,
  ROUND(
    100.0 * SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) / COUNT(*),
    3
  ) AS availability_pct
FROM public.uptime_checks
GROUP BY 1
ORDER BY 1 DESC;
```

---

## 4. 月次品質レポート仕様

### 4.1 レポート構成

```
docs/QUALITY_REPORT_YYYY-MM.md
├── 1. SLA 達成状況サマリー（稼働率・レスポンス・エラー率）
├── 2. ビジネス KPI（診断件数・精度・DAU/WAU）
├── 3. インフラコスト実績（Gemini / Firebase / Supabase）
├── 4. インシデント一覧（発生 P1/P2/P3 件数・MTTR）
├── 5. 翌月の改善アクション
└── 6. 参照: ポストモーテム・GitHub Issues
```

### 4.2 自動生成スクリプト仕様（T764 で実装）

```python
# scripts/generate_monthly_quality_report.py
# 実行: python scripts/generate_monthly_quality_report.py --month 2026-06
#
# 処理フロー:
# 1. Supabase から kpi_daily_diagnoses / kpi_weekly_active_users を取得
# 2. Google Cloud Monitoring API から Uptime Check データを取得
# 3. Sentry API からエラー率・インシデント数を取得
# 4. GCP Billing API から月間コスト実績を取得
# 5. docs/QUALITY_REPORT_{YYYY-MM}.md を自動生成
# 6. Google Sheets の「月次KPIレポート」タブに書き込み
```

---

## 5. アラート閾値と通知設定

| 指標 | 警告（Warning） | 緊急（Critical） | 通知先 |
| :--- | :--- | :--- | :--- |
| 稼働率（直近24h） | < 99.8% | < 99.0% | Slack #alerts |
| P95 レスポンス | > 2.0 秒 | > 5.0 秒 | Slack #alerts |
| 5xx エラー率（直近1h） | > 1.0% | > 5.0% | Slack #alerts + メール |
| Gemini API コスト | $40/月 | $50/月 | メール |
| Supabase DB 使用量 | 400 MB | 480 MB | Slack #alerts |

---

## 6. SLA 違反時の対応フロー

SLA 違反（稼働率 < 99.5%）が確認された場合：

1. **即時**: Slack #alerts に自動通知（Google Cloud Monitoring アラートポリシー）
2. **24時間以内**: 根本原因分析（RCA）を実施し、[INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) に従って `docs/POSTMORTEM_YYYY-MM-DD_<ID>_<SLUG>.md` を作成
3. **翌月の月次レポート**: SLA 違反の経緯・影響・再発防止策を記載

---

## 7. 関連ドキュメント

- [災害復旧・エスカレーション連絡網ランブック](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [Firebase / Supabase システムアーキテクチャ詳細設計書](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md)
- [Supabase Database 物理設計とインデックス設計](SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md)
