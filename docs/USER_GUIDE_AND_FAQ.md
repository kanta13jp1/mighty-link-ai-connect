# 📘 Mighty Skill-Bridge: ユーザー操作ガイド・FAQ・管理者トラブルシューティング手順書

> **対象読者**: 一般ユーザー（人材担当・営業担当）、システム管理者  
> **最終更新**: 2026-06-20
> **バージョン**: v1.2.0
> **関連タスク**: T744 / T790 / T781

---

## 目次

1. [ユーザー向け操作ガイド](#1-ユーザー向け操作ガイド)
   - [1.1 サービス概要](#11-サービス概要)
   - [1.2 ログイン・初回アクセス](#12-ログイン初回アクセス)
   - [1.3 AIフィット診断の実行手順](#13-aiフィット診断の実行手順)
   - [1.4 診断結果の見方](#14-診断結果の見方)
   - [1.5 案件候補ストック管理](#15-案件候補ストック管理)
   - [1.6 問い合わせ窓口](#16-問い合わせ窓口)
2. [よくある質問（FAQ）](#2-よくある質問faq)
3. [管理者向けトラブルシューティング手順書](#3-管理者向けトラブルシューティング手順書)
   - [3.1 システム構成の概要](#31-システム構成の概要)
   - [3.2 障害種別と対処手順](#32-障害種別と対処手順)
   - [3.3 定期メンテナンス手順](#33-定期メンテナンス手順)
   - [3.4 エスカレーション基準](#34-エスカレーション基準)

---

## 1. ユーザー向け操作ガイド

### 1.1 サービス概要

**Mighty Skill-Bridge** は、エンジニアの経歴書（スキルシート）と案件の募集要項を AI が多角的に分析し、4つの軸でフィット度を可視化する **AIフィットシミュレーター** です。

| 機能 | 説明 |
|:---|:---|
| **4軸フィット診断** | Skill / Culture / Growth / Performing の4軸でマッチ度を数値化 |
| **matched/missing スキル可視化** | 案件と合致するスキルと不足スキルをUI上で即確認 |
| **面談想定質問生成** | AIが面談で想定される深掘り質問と模範回答を自動生成 |
| **案件候補ストック管理** | 複数エンジニア × 複数案件の突合ビューをダッシュボードで管理 |

---

### 1.2 ログイン・初回アクセス

#### アクセスURL

| 環境 | URL |
|:---|:---|
| 本番（公開デモ） | `https://kanta13jp1.github.io/mighty-link-ai-connect/` |
| ローカル開発 | `http://localhost:8000` |

#### ログイン手順

1. ブラウザでアクセスURLを開く
2. **Basic認証ダイアログ**が表示される
   - ユーザー名・パスワードを管理者から受け取り入力する
3. 初回ログイン時は**利用同意書**への同意が必要
   - 「個人情報の取り扱いについて同意する」チェックボックスを確認
   - 「同意して開始」ボタンをクリック

> ⚠️ **注意**: 経歴書には個人情報が含まれます。アップロード前に氏名・連絡先等がマスキングされていることを確認してください。

---

### 1.3 AIフィット診断の実行手順

#### Step 1: スキルシート（経歴書）のアップロード

1. トップ画面の「**エンジニア経歴書をドロップ**」エリアにファイルをドラッグ＆ドロップ
   - 対応形式: PDF / Word (.docx) / 画像 (.png, .jpg)
   - 最大ファイルサイズ: 10 MB
2. アップロード完了後、プレビューパネルに内容の要約が表示される

#### Step 2: 案件定義書の入力

以下のいずれかの方法で案件情報を入力します:

- **ドロップ方式**: 「**案件票をドロップ**」エリアにPDFファイルをドロップ
- **テキスト方式**: テキストエリアに案件の要件を直接貼り付け

#### Step 3: AI診断の実行

1. 「**AIフィット診断を実行**」ボタンをクリック
2. ローディングアニメーション（通常 3〜10 秒）が表示される
3. 診断結果画面に自動遷移

#### Step 4: 結果の確認と保存

1. 診断結果を確認（詳細は[1.4 診断結果の見方](#14-診断結果の見方)参照）
2. 「**Google Sheets に保存**」ボタンで結果を台帳へ記録（オプション）
3. 「**PDFで出力**」ボタンで印刷用レポートを生成（オプション）

---

### 1.4 診断結果の見方

#### レーダーチャート（4軸スコア）

中央のレーダーチャートには以下の4軸スコア（0〜100）が表示されます:

| 軸 | 英語名 | 意味 |
|:---|:---|:---|
| **スキル適合** | Skill Fit | 技術スタック・フレームワークのマッチ度 |
| **カルチャー適合** | Culture Fit | 開発文化（アジャイル/ウォーターフォール等）の親和性 |
| **グロース適合** | Growth Fit | キャリア目標と案件の将来性の整合性 |
| **パフォーミング** | Performing Fit | 即戦力としての稼働想定生産性 |

#### マッチ/ミスマッチスキル一覧

- 🟢 **matched_skills**: 案件要件と合致しているスキル
- 🔴 **missing_skills**: 案件要件に対して不足しているスキル
- 🟡 **partial_match**: 一部合致しているスキル（要確認）

#### 面談想定質問

AIが自動生成した面談質問と模範解答が表示されます。  
担当者は面談前の準備資料として活用できます。

---

### 1.5 案件候補ストック管理

複数のエンジニアと複数の案件を一覧で比較できるダッシュボードです。

1. ナビゲーションメニューから「**案件ストック管理**」を選択
2. 登録済みの診断結果が一覧で表示される
3. 列ヘッダーをクリックしてスコア順に並び替え可能
4. 「**比較ビュー**」ボタンで最大4名のエンジニアを横並び比較

---

### 1.6 問い合わせ窓口

問い合わせは、アプリ下部の **問い合わせ窓口** フォームまたは暫定メール窓口 `k-umezawa@ml-mightylink.com` で受け付けます。

| 種別 | 主な内容 | 初回返信目安 |
|:---|:---|:---|
| 一般 | 操作方法、利用相談、軽微な確認 | 1営業日以内 |
| 技術不具合 | 診断エラー、画面不具合、API失敗 | 当日〜1営業日以内 |
| 請求 | 有償化後のプラン・請求・領収書 | 1営業日以内 |
| 個人情報 | 経歴書・個人情報の削除/確認 | 当日一次確認 |
| 診断改善 | 診断結果への改善要望、NPSコメント補足 | 2営業日以内 |

フォーム送信内容は `support_requests` テーブルに保存され、管理者のみが `GET /api/support/summary` で確認します。GitHub Pages の静的デモ環境では API が存在しないため、送信できない場合はメール窓口を使ってください。

---

## 2. よくある質問（FAQ）

### Q1. アップロードできるファイル形式は？

**A**: PDF / Word (.docx) / 画像 (.png, .jpg) に対応しています。Excel (.xlsx) は現時点で非対応です。Word形式の場合はPDFに変換してからアップロードすることを推奨します。

---

### Q2. 診断結果の精度はどの程度ですか？

**A**: AIによる解析は補助ツールとして設計されています。社内パイロット（2026年6月）では、担当者の事前準備工数を約70%削減できる見込みが確認されています。ただし最終判断は必ず人間が行ってください。

---

### Q3. 経歴書のデータはどこに保存されますか？

**A**: アップロードされた経歴書は診断処理のためのみ一時的に使用されます。処理完了後はサーバー上の一時ファイルから削除されます。診断スコアと要約データのみが Supabase データベースに保存されます（個人を特定できる情報は保存しません）。

---

### Q4. パイロット期間終了後、データは削除されますか？

**A**: パイロット参加者の同意書に記載のとおり、パイロット終了後3営業日以内にすべての個人情報関連データを完全消去します。詳細は[利用同意書テンプレート](PILOT_CONSENT_TEMPLATE.md)を参照してください。

---

### Q5. 診断が途中で止まった・エラーになった場合は？

**A**: 以下を順に試してください:
1. ページをリロード（F5）して再試行
2. ブラウザのキャッシュをクリア（Ctrl+Shift+R）
3. 別のブラウザ（Chrome 推奨）で試す
4. ファイルサイズが 10 MB を超えていないか確認
5. 解決しない場合は管理者（`k-umezawa@ml-mightylink.com`）に連絡

---

### Q6. Gemini APIが使えない場合でも動作しますか？

**A**: はい。Gemini API が利用できない場合でも、`deterministic_fallback` モードで動作します。この場合、AIによる自然言語解析は実行されませんが、ルールベースのスキル抽出と4軸スコアリングは継続されます。

---

### Q7. 診断結果を Google Sheets に保存できますか？

**A**: 「Google Sheets に保存」ボタンが表示されている場合は、管理者が Google Workspace 連携を有効化しています。ボタンが表示されない場合は Sheets 連携が無効です。管理者に確認してください。

---

### Q8. 複数の案件を同時に比較するには？

**A**: 各案件で診断を実行した後、ナビゲーションの「案件ストック管理」から「比較ビュー」を使用してください。最大4件まで同時に横並び比較ができます。

---

### Q9. 問い合わせへの回答状況はどこで確認されますか？

**A**: 管理者は Basic Auth 付きの `GET /api/support/summary` で新規件数、優先度、カテゴリ、直近問い合わせの抜粋を確認します。返信は暫定メール窓口 `k-umezawa@ml-mightylink.com` から行い、仕様変更・不具合・法務確認が必要なものは `data/issues_tracker.tsv` と GitHub Issues へ起票します。

---

### Q10. 自分のデータをエクスポートできますか？

**A**: T781のPoCとして、Firebase Authで本人確認したユーザーは問い合わせ欄の「ユーザーデータ JSON」または `GET /api/user-data/export` からJSON形式でセルフエクスポートできます。問い合わせは本人メール、診断フィードバックとマッチ履歴はブラウザセッションIDに紐づく範囲だけを返します。現行デモの `engineers` / `jobs` / `match_results` にはまだ恒久的な `owner_uid` が無いため、T752のオンボーディング整備で所有者カラムを追加してから一般公開・有償ローンチの標準機能にします。

---

## 3. 管理者向けトラブルシューティング手順書

### 3.1 システム構成の概要

```
[ブラウザ SPA]
    │
    ├─ Firebase Hosting (静的ファイル配信)
    │
    ├─ Firebase Auth (認証)
    │
    └─ Firebase Cloud Functions (API エンドポイント / Python)
            │
            ├─ Supabase PostgreSQL + RLS (データ永続化)
            │
            └─ Gemini API (AI解析 / fallback付き)
```

| コンポーネント | URL / 管理コンソール |
|:---|:---|
| Firebase Console | `https://console.firebase.google.com/project/my-web-app-b67f4` |
| Supabase Dashboard | `https://supabase.com/dashboard/project/<project_id>` |
| GitHub Actions (CI/CD) | `https://github.com/kanta13jp1/mighty-link-ai-connect/actions` |
| 公開デモ URL | `https://kanta13jp1.github.io/mighty-link-ai-connect/` |
| 管理者ダッシュボード | `http://localhost:8000/admin` (ローカル) |
| 問い合わせサマリAPI | `/api/support/summary` (Basic Auth必須) |
| ユーザーデータエクスポートAPI | `/api/user-data/export` (Firebase Auth必須) |

---

### 3.2 障害種別と対処手順

#### 🔴 P1: サービス全体停止

**症状**: 公開URLにアクセスできない、502/503エラー

**確認手順**:
```powershell
# GitHub Actions の最新デプロイ状態確認
gh run list --limit 5 --repo kanta13jp1/mighty-link-ai-connect

# Firebase Hosting 状態確認
firebase hosting:channel:list

# 公開デモガード実行
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

**対処**:
1. GitHub Actions の最新ワークフロー失敗ログを確認
2. 前回成功したデプロイへロールバック: `firebase hosting:clone SOURCE:live TARGET:live`
3. 解決しない場合は Firebase コンソールで手動デプロイ

---

#### 🔴 P1: Firebase Auth 認証不可

**症状**: ログイン画面でエラー、全ユーザーがログインできない

**確認手順**:
```powershell
# Firebase Auth の状態確認
firebase auth:export --format=json auth_export.json 2>&1 | head -5
# → エラーなければ Auth サービス自体は生きている
```

**対処**:
1. Firebase Console → Authentication → ステータスを確認
2. `FIREBASE_API_KEY` 環境変数が正しく設定されているか確認
3. Firebase Status Page (`https://status.firebase.google.com/`) で障害情報を確認

---

#### 🟠 P2: AI診断が実行されない（Gemini API エラー）

**症状**: 診断ボタンを押してもエラーまたは空の結果が返る

**確認手順**:
```powershell
# APIキーの有効性確認（コスト監視スクリプト）
python scripts/monitor_managed_agents_cost.py --check-only

# 監査ログで直近のエラーを確認
python -c "import json; [print(l) for l in open('data/audit/api_audit.jsonl') if 'error' in l]" 2>$null | Select-Object -Last 10
```

**対処**:
1. `GEMINI_API_KEY` の有効期限・クォータを Google AI Studio で確認
2. クォータ超過の場合: `deterministic_fallback` モードに自動切替済みのため診断機能は継続動作
3. キーを更新した場合は `.env` ファイルと GitHub Secrets の両方を更新

---

#### 🟠 P2: Supabase DB 接続失敗

**症状**: 診断結果が保存されない、`data/mighty.db` (SQLite) へのフォールバックが発生

**確認手順**:
```powershell
# Supabase接続確認
python -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'])
print('OK:', conn.server_version)
conn.close()
"

# アクティブな接続数確認（Supabase Dashboardでも可）
```

**対処**:
1. Supabase Dashboard → Settings → Database → 接続情報を再確認
2. `SUPABASE_DB_URL` / `SUPABASE_ANON_KEY` 環境変数を確認
3. PgBouncer 接続プールが上限に達している場合: 不要なセッションを終了

---

#### 🟡 P3: Google Sheets/Calendar 同期失敗

**症状**: WBS更新がスプレッドシートに反映されない

**確認手順**:
```powershell
# 認証アカウント確認
python scripts/verify_google_workspace_account.py

# 手動同期実行（エラーメッセージを確認）
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8 2>&1
```

**対処**:
1. `authorized_user.json` の有効期限切れ・取り消し → `python scripts/verify_google_workspace_account.py --reauth` で `k-umezawa@ml-mightylink.com` に再認証
2. スプレッドシートIDが正しいか確認（`1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8`）
3. 連携アカウントが `k-umezawa@ml-mightylink.com` であることを確認

詳細手順: [Google Workspace OAuth 再認証 Runbook](GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md)

---

#### 🟠 P2/P3: 問い合わせ対応遅延

**症状**: `support_requests` の `new` が未確認のまま残る、技術不具合/個人情報カテゴリの一次確認が遅れる

**確認手順**:
```powershell
# Basic Auth付きで問い合わせキューを確認
$pair = "$env:BASIC_AUTH_USERNAME`:$env:BASIC_AUTH_PASSWORD"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
Invoke-WebRequest -Uri "http://localhost:8000/api/support/summary" -Headers @{Authorization = "Basic $auth"} -UseBasicParsing
```

**対処**:
1. `GET /api/support/summary` の `priority_counts.high/urgent` と `category_counts.technical/privacy` を確認
2. 技術不具合・個人情報・請求は、同日中に一次返信し `data/issues_tracker.tsv` へ起票
3. サービス停止・個人情報漏えい疑い・課金誤請求は P1/P2 として [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) に接続

---

#### 🟡 P3: CI/CD デプロイ失敗（GitHub Actions）

**症状**: push後に本番反映されない

**確認手順**:
```powershell
# 最新ワークフロー状態
gh run list --limit 5

# 失敗したジョブのログ取得
gh run view <run-id> --log-failed
```

**対処**:
1. Python バージョン不一致 → `.python-version` と `deploy.yml` の python-version を確認
2. Firebase トークン期限切れ → GitHub Secrets の `FIREBASE_TOKEN` を更新
3. 依存関係エラー → `requirements.txt` の freeze状態を確認

---

### 3.3 定期メンテナンス手順

#### 日次（毎朝 9:00 JST）

```powershell
# コスト台帳監査
python scripts/monitor_managed_agents_cost.py

# 監査ログのローテーション確認
Get-Item data\audit\*.jsonl | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name, Length

# 問い合わせキュー確認
# GET /api/support/summary を管理者認証付きで確認し、未対応があれば課題管理表へ反映
```

#### 週次（毎週月曜日）

```powershell
# WBS → Sheets 同期
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8

# 完了タスクのカレンダーイベント削除
python scripts/sync_wbs_to_calendar.py

# 公開デモガード実行
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

#### 月次（毎月第1営業日）

```powershell
# NotebookLM ドキュメント同期
python scripts/sync_docs_to_notebooklm.py

# CEO向けプレゼンデッキ更新
python scripts/generate_ceo_presentation_deck.py

# Drive アップロード
python scripts/upload_notebooklm_docs_to_drive.py

# 古いドキュメントの棚卸し（該当ファイルを削除/更新）
```

#### 四半期ごと

- Firebase / Supabase のセキュリティルール見直し
- Gemini APIモデルバージョン確認と最新版への移行検討
- `requirements.txt` の依存ライブラリ脆弱性スキャン（`pip-audit`）
- コスト実績のCEOへの報告

---

### 3.4 エスカレーション基準

| 優先度 | 条件 | 初動対応時間 | エスカレーション先 |
|:---:|:---|:---:|:---|
| **P1** | サービス全体停止・認証全断 | 30分以内 | 開発担当 → 即座にSlack通知 |
| **P2** | AI診断不可・DB接続失敗・個人情報漏えい疑い・課金誤請求 | 2時間以内 | 開発担当へ報告、必要に応じてCEOへ共有 |
| **P3** | Sheets同期失敗・デプロイ遅延・通常問い合わせ未返信 | 翌営業日 | 定例レビューで報告 |
| **P4** | ドキュメント誤記・UI軽微バグ | 1週間以内 | GitHub Issues へ起票 |

#### 連絡先

| 役割 | 連絡先 |
|:---|:---|
| システム管理者 | `k-umezawa@ml-mightylink.com` |
| 開発担当（Claude Code） | VSCode Claude Code セッションを起動 |
| 開発担当（Codex） | VSCode Codex セッションを起動 |

---

## 付録: 関連ドキュメント一覧

| ドキュメント | 内容 |
|:---|:---|
| [FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md) | システムアーキテクチャ詳細設計 |
| [FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md](FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md) | セキュリティ設計 |
| [SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md](SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md) | DB物理設計 |
| [PILOT_CONSENT_TEMPLATE.md](PILOT_CONSENT_TEMPLATE.md) | 個人情報同意書テンプレート |
| [PILOT_REPORT_2026-06-16.md](PILOT_REPORT_2026-06-16.md) | パイロット結果サマリ |
| [SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md](SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md) | 問い合わせ窓口・SLA・エスカレーション運用 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 環境構築手順書 |
| [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) | 3ツール開発ワークフロー |
