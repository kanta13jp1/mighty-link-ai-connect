# 月次進捗レポート・KPIダッシュボード整備仕様 (T767)

ステークホルダー（社長・投資家・開発チーム）向けの月次進捗レポートと、Google Sheets による KPI ダッシュボードの整備仕様を定義します。

---

## バージョン履歴

| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-10 | v1.0.0 | 初版作成（レポート構成・Sheets設計・自動投稿フロー） | Claude Code |

---

## 1. 月次進捗レポート構成

### 1.1 レポートファイル命名規則

```
docs/MONTHLY_REPORT_YYYY-MM.md
```

### 1.2 レポートテンプレート

```markdown
# Mighty Skill-Bridge 月次進捗レポート: YYYY年MM月

**作成日**: YYYY-MM-DD
**作成者**: 梅澤 寛太（+ Claude Code）

---

## エグゼクティブサマリー

[3〜5行で今月の最大トピックを箇条書き]

---

## 1. WBS 進捗

| 指標 | 今月 | 先月比 |
| :--- | :--- | :--- |
| 完了タスク数 | XX 件 | +XX 件 |
| 完了率 | XX.X% | +X.X pt |
| 予定対比 | X 日前倒し / X 日遅延 | — |

[未完了タスクで当月中に完了すべきだったもの]

---

## 2. サービス品質 KPI

| KPI | 今月実績 | 目標 | 達成 |
| :--- | :--- | :--- | :--- |
| 稼働率 | XX.XX% | ≥99.5% | ✅/❌ |
| P95 レスポンス | X.X 秒 | ≤3.0 秒 | ✅/❌ |
| 5xx エラー率 | X.XX% | ≤0.5% | ✅/❌ |
| 診断実行件数 | XX 件 | ≥5件/週 | ✅/❌ |
| 診断精度スコア | XX% | ≥70% | ✅/❌ |

---

## 3. インフラコスト実績

| サービス | 今月費用 | 予算 | 状況 |
| :--- | :--- | :--- | :--- |
| Gemini API | $XX.XX | ≤$50 | ✅/⚠️/❌ |
| Firebase (Hosting/Functions) | $XX.XX | ≤$30 | ✅/⚠️/❌ |
| Supabase | $XX.XX | ≤$25 | ✅/⚠️/❌ |
| **合計** | **$XX.XX** | **≤$105** | ✅/⚠️/❌ |

---

## 4. インシデント・課題

| 日付 | レベル | 概要 | 状態 |
| :--- | :--- | :--- | :--- |
| [なし] | — | — | — |

---

## 5. 翌月の優先アクション

1. [タスクID] タスク名（担当: XXX）
2. [タスクID] タスク名（担当: XXX）
3. [タスクID] タスク名（担当: XXX）

---

## 6. 参照リンク

- [WBS スプレッドシート](https://docs.google.com/spreadsheets/d/1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8)
- [GitHub リポジトリ](https://github.com/kanta13jp1/mighty-link-ai-connect)
- [公開デモ URL](https://kanta13jp1.github.io/mighty-link-ai-connect/)
```

---

## 2. Google Sheets KPIダッシュボード設計

### 2.1 シート構成（スプレッドシート内タブ）

| タブ名 | 内容 | 更新頻度 |
| :--- | :--- | :--- |
| **WBS** | タスク一覧・進捗・ガントチャート | セッション毎 |
| **月次KPIサマリー** | 月別 KPI 実績テーブル + スパークライン | 月次 |
| **稼働率トレンド** | 日別稼働率グラフ（折れ線） | 月次 |
| **コストトレンド** | サービス別月次コスト積み上げグラフ | 月次 |
| **診断件数推移** | 日次診断件数 + 累計グラフ | 月次 |
| **課題管理表** | GitHub Issues 連携・P1〜P4 一覧 | セッション毎 |
| **QA表** | テストケース・結果・未解決バグ | セッション毎 |

### 2.2 月次KPIサマリー タブのスキーマ

```
月	稼働率(%)	P95レスポンス(s)	5xxエラー率(%)	診断件数	精度スコア(%)	Gemini費用($)	Firebase費用($)	Supabase費用($)	合計費用($)
2026-05	—	—	—	—	—	—	—	—	—
2026-06	99.9	1.8	0.1	12	76	8.50	0	0	8.50
```

### 2.3 自動更新スクリプト仕様

```python
# scripts/sync_monthly_kpi_to_sheets.py
# 実行: python scripts/sync_monthly_kpi_to_sheets.py --month 2026-06
#
# 処理フロー:
# 1. Supabase: kpi_daily_diagnoses ビューから月次集計
# 2. Google Cloud Monitoring API: Uptime Check から稼働率取得
# 3. Sentry API: エラー率・インシデント数取得
# 4. GCP Billing API: 月間コスト取得
# 5. Sheets「月次KPIサマリー」タブに1行追記
# 6. グラフ範囲を自動拡張
```

---

## 3. Notion への自動投稿フロー

月次レポートを Notion のプロジェクトページにも自動投稿する。

```python
# scripts/post_report_to_notion.py
# Notion API: https://api.notion.com/v1/pages
#
# 必要環境変数:
#   NOTION_API_KEY: Notion Integration Token
#   NOTION_DATABASE_ID: 月次レポートデータベースのID
#
# 処理:
# 1. docs/MONTHLY_REPORT_YYYY-MM.md を読み込み
# 2. Markdown → Notion ブロックに変換
# 3. Notion データベースに新規ページとして投稿
# 4. 投稿URLをSlack #dev-reports チャンネルに通知
```

---

## 4. Slack 月次レポート通知

毎月1日の AM 09:00 JST に月次レポートのサマリーを自動送信する。

```python
# scripts/send_monthly_slack_report.py
# Slack Incoming Webhook を使用
#
# 送信先: #dev-reports チャンネル
# 送信内容:
#   📊 [YYYY年MM月] Mighty Skill-Bridge 月次レポート
#   ✅ WBS 完了率: XX.X% (+X.Xpt)
#   📈 稼働率: XX.XX% | P95: X.Xs | 診断件数: XX件
#   💰 月間コスト: $XX.XX / $105 (XX%)
#   🔗 詳細: [Sheets URL] | [GitHub URL]
```

---

## 5. 実施スケジュール

| タイミング | アクション | 実行方法 |
| :--- | :--- | :--- |
| 毎月末日 | KPI データ収集・集計 | `sync_monthly_kpi_to_sheets.py` |
| 翌月1日 AM 07:00 | `docs/MONTHLY_REPORT_YYYY-MM.md` 生成 | `generate_monthly_quality_report.py`（T764） |
| 翌月1日 AM 09:00 | Slack 通知送信 | `send_monthly_slack_report.py` |
| 翌月1日 AM 10:00 | Notion 投稿 | `post_report_to_notion.py` |

---

## 6. 関連ドキュメント

- [SLA/KPI 定義と計測基盤整備](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [災害復旧・エスカレーション連絡網ランブック](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
