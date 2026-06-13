# 四半期セキュリティ監査ランブック (T774)

**Mighty Skill-Bridge** 本番環境の四半期セキュリティ監査手順書です。静的解析・依存ライブラリ脆弱性・RLSポリシー・シークレット漏洩の4軸で監査を実施します。

---

## バージョン履歴

| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-10 | v1.0.0 | 初版作成（4軸監査チェックリスト・自動化スクリプト仕様） | Claude Code |
| 2026-06-11 | v1.1.0 | 初回監査(2026-Q2)実施に伴う更新: 対象パスを実構成 (src/ scripts/ main.py) へ修正、firebase_uid を public スキーマ表記へ統一、Actions SHA ピン留め推奨を追記 | Claude Code |
| 2026-06-12 | v1.2.0 | 初回監査(2026-Q2)完了。結果は [SECURITY_AUDIT_REPORT_2026-Q2.md](SECURITY_AUDIT_REPORT_2026-Q2.md) に記録（T789 / R49 / R50 / SEC-004〜007）。次回監査は 2026-09 | Claude Code |
| 2026-06-12 | v1.3.0 | T747完了: Dependabot (`pip` / `github-actions`) と週次 `security-scan.yml`（Bandit / pip-audit）を追加。既知未修正事項は T802 / Issue #72 で追跡 | Codex |

---

## 1. 監査スケジュール

| 実施タイミング | 実施内容 | 担当 |
| :--- | :--- | :--- |
| **四半期**（3 / 6 / 9 / 12月） | 全4軸フル監査 | 開発担当 + Claude Code |
| **週次**（月曜 07:00 JST） | GitHub Actions `Weekly Security Scan` による Bandit / pip-audit 実行 | 自動（CI） |
| **月次** | Dependabot PR と GitHub security alerts の確認 | 開発担当 |
| **対象 PR** | Python / requirements / security workflow 変更時の Bandit / pip-audit 実行 | 自動（CI） |

---

## 2. 監査軸1：静的解析（SAST）

### 2.1 ツール

| ツール | 対象言語 | 用途 |
| :--- | :--- | :--- |
| Bandit | Python | SQLインジェクション・コマンドインジェクション・ハードコードシークレット検出 |
| Semgrep | Python / JavaScript | OWASP Top 10 ルールセットによる脆弱性スキャン |
| ESLint (security plugin) | JavaScript / TypeScript | XSS・Prototype Pollution 検出 |

### 2.2 実行手順

```bash
# Python 静的解析（対象は src/ scripts/ main.py — functions/ ディレクトリは存在しない）
pip install bandit semgrep
bandit -r src/ scripts/ main.py -ll -f txt -o reports/bandit_YYYY-QQ.txt

# Semgrep（OWASP ルールセット）
semgrep --config=p/owasp-top-ten --output=reports/semgrep_YYYY-QQ.txt src/ scripts/ main.py

# JavaScript 静的解析
npx eslint --plugin security --rule 'security/detect-object-injection: error' exports/
```

### 2.3 合否判定

| 重大度 | 対応要件 |
| :--- | :--- |
| High / Critical | 発見後 **72時間以内** に修正・再スキャン |
| Medium | 次のスプリント内（1週間以内）に対応 |
| Low / Info | 月次レビュー時に対応可否を判断 |

---

## 3. 監査軸2：依存ライブラリ脆弱性スキャン

### 3.1 ツール

| ツール | 対象 | 用途 |
| :--- | :--- | :--- |
| GitHub Dependabot | Python / GitHub Actions | 脆弱性検知・自動 PR 作成（T747 で設定） |
| pip-audit | Python | `requirements.txt` の CVE 照合 |
| npm audit | Node.js | `package.json` の CVE 照合 |
| OWASP Dependency-Check | 全依存ライブラリ | NVD データベースとの照合 |

### 3.2 実行手順

```bash
# Python 依存ライブラリ監査
pip install pip-audit
pip-audit -r requirements.txt -o reports/pip_audit_YYYY-QQ.json --format json

# npm 依存ライブラリ監査（フロントエンドがある場合）
npm audit --audit-level=moderate --json > reports/npm_audit_YYYY-QQ.json
```

### 3.3 合否判定

| CVSSスコア | 対応要件 |
| :--- | :--- |
| CVSS ≥ 9.0 (Critical) | **即時対応**（本番デプロイを一時停止） |
| CVSS 7.0〜8.9 (High) | 発見後 **1週間以内** にパッチ適用 |
| CVSS 4.0〜6.9 (Medium) | 次の定期メンテナンス時 |
| CVSS < 4.0 (Low) | 四半期監査時にまとめて対応 |

---

## 4. 監査軸3：Supabase RLS ポリシー検証

### 4.1 チェックリスト

```text
[ ] 全テーブルで ALTER TABLE ... ENABLE ROW LEVEL SECURITY が設定されている
[ ] SELECT / INSERT / UPDATE / DELETE の各操作に明示的なポリシーが存在する
[ ] フロントエンドからの直接 DELETE は profiles テーブルで禁止されている
[ ] public.firebase_uid() = user_id による所有者チェックが実装されている（本番では auth スキーマへの関数作成不可のため public スキーマに配置）
[ ] RLS ポリシーが JWT の user_metadata クレームを参照していない（ユーザー改変可能なため禁忌）
[ ] Service Role Key を使用する操作は Cloud Functions のみに限定されている
[ ] anon ロールが個人情報テーブルへのアクセス権を持っていない
```

### 4.2 自動テスト実行

```bash
# T733_2 で作成した RLS ユニットテストを実行
pytest tests/test_rls_policies.py -v --tb=short

# Supabase CLI でローカル RLS 検証
supabase db test
```

### 4.3 RLS ポリシー一覧の確認クエリ

```sql
-- 全テーブルの RLS 有効状態確認
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 全ポリシー一覧
SELECT
  schemaname, tablename, policyname, permissive,
  roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
```

---

## 5. 監査軸4：シークレット漏洩検知

### 5.1 ツール

| ツール | 用途 |
| :--- | :--- |
| truffleHog | Git 全履歴のシークレットスキャン |
| gitleaks | 高速シークレット検出（CI 組み込み用） |
| git-secrets | コミット前フック（pre-commit） |

### 5.2 実行手順

```bash
# Git 全履歴スキャン（四半期監査時）
pip install trufflehog
trufflehog git file://. --json > reports/trufflehog_YYYY-QQ.json

# 高速スキャン（CI 組み込み用）
brew install gitleaks   # または pip install gitleaks-py
gitleaks detect --source . --report-path=reports/gitleaks_YYYY-QQ.json

# 検出ルールの追加（API キーパターン）
# .gitleaks.toml に Gemini / Supabase / Firebase のキーパターンを追加
```

### 5.3 .gitleaks.toml 設定例

```toml
[allowlist]
  description = "Global allowlist"
  paths = [
    '''\.env\.example''',
    '''docs/.*''',
  ]

[[rules]]
  description = "Supabase Service Role Key"
  id = "supabase-service-role"
  regex = '''eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'''
  tags = ["supabase", "jwt"]

[[rules]]
  description = "Firebase API Key"
  id = "firebase-api-key"
  regex = '''AIza[0-9A-Za-z\-_]{35}'''
  tags = ["firebase"]
```

### 5.4 シークレット漏洩時の対応（緊急手順）

```text
1. 漏洩したキーを **即時ローテーション**（GCP / Supabase / Firebase ダッシュボードで新鍵発行）
2. Git 履歴から削除: git filter-repo --path <file> --invert-paths
3. GitHub に強制 push: git push --force-with-lease
4. GitHub に連絡してキャッシュ削除を依頼
5. インシデントレポートを作成（[INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) に従い `docs/POSTMORTEM_YYYY-MM-DD_<ID>_<SLUG>.md` を作成）
6. アクセスログを確認して不正利用がないか検証
```

---

## 6. 監査レポートテンプレート

```markdown
# セキュリティ監査レポート: YYYY-Q[1-4]

## 実施日: YYYY-MM-DD
## 実施者: 梅澤 寛太

## サマリー

| 軸 | 結果 | 検出件数 | 未解決 |
| :--- | :--- | :--- | :--- |
| 静的解析 (Bandit/Semgrep) | ✅ PASS / ❌ FAIL | 0件 | 0件 |
| 依存ライブラリ脆弱性 | ✅ PASS / ❌ FAIL | 0件 | 0件 |
| RLS ポリシー検証 | ✅ PASS / ❌ FAIL | 0件 | 0件 |
| シークレット漏洩 | ✅ PASS / ❌ FAIL | 0件 | 0件 |

## 検出事項と対応状況

[高・中・低 の各項目を記載]

## 次回監査予定: YYYY-MM-DD
```

---

## 7. CI/CD への組み込み（GitHub Actions）

```yaml
# .github/workflows/security-scan.yml（抜粋）
name: Weekly Security Scan
"on":
  schedule:
    - cron: "0 22 * * 0" # Monday 07:00 JST
  workflow_dispatch:
  pull_request:
    paths:
      - "requirements.txt"
      - "src/**/*.py"
      - "scripts/**/*.py"
      - "main.py"

jobs:
  python-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
      - run: python -m pip install bandit pip-audit
      - run: bandit -r src scripts main.py -ll
      - run: pip-audit -r requirements.txt --format json
```

> [!NOTE]
> **サードパーティ action は full commit SHA へのピン留めを推奨**（2026-03 の tj-actions/trivy-action 系サプライチェーン攻撃でタグ改ざんによる secrets 流出が実証された）。T747の週次スキャンは新規サードパーティ action を増やさず、GitHub公式 action と Python CLI (`bandit` / `pip-audit`) で構成する。GitHub Actions の version update は `.github/dependabot.yml` の `github-actions` エコシステム監視で運用する。

---

## 8. 関連ドキュメント

- [システム監査ログ 氏名マスキング・暗号化パイプライン設計書](AUDIT_LOG_MASKING_AND_ENCRYPTION.md)
- [災害復旧・エスカレーション連絡網ランブック](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [SLA/KPI 定義と計測基盤整備](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [Firebase / Supabase セキュリティ設計](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md)
