# セキュリティ監査レポート: 2026-Q2（初回）

**Mighty Skill-Bridge** 本番環境の四半期セキュリティ監査（初回 / T789）の結果報告です。
[四半期セキュリティ監査ランブック](SECURITY_AUDIT_RUNBOOK.md) の 4 軸チェックリストに準拠して実施しました。

- **実施日**: 2026-06-12
- **実施者**: Claude Code（VSCode + Claude Code レーン） + 梅澤 寛太
- **対象**: `src/` `scripts/` `main.py`（Python 10,304 行）、`requirements.txt` 依存 88 パッケージ、`supabase/migrations/`、Git 追跡ファイル全件

---

## サマリー

| 軸 | 結果 | 検出件数 | 未解決 |
| :--- | :--- | :--- | :--- |
| 静的解析 (Bandit 1.9.4) | ❌ FAIL → 修正済 | High 1 / Medium 20 / Low 24 | Medium 20（R50 で対応中） |
| 依存ライブラリ脆弱性 (pip-audit 2.10.1) | ❌ FAIL | CVE 1 件 (starlette) | 1 件（R49 で対応中） |
| RLS ポリシー検証 (pytest + SQL レビュー) | ✅ PASS | 0 件 | 0 件 |
| シークレット漏洩 (パターンスキャン + git 追跡確認) | ✅ PASS | 0 件（誤検知 1 件のみ） | 0 件 |

**総合判定**: 条件付き PASS — High 検出は監査セッション内で修正完了。未解決の R49（starlette CVE）/ R50（requests timeout）は新規タスク T802 でランブック SLA（1 週間）内に修正する。

---

## 1. 静的解析（Bandit）

`bandit -r src/ scripts/ main.py -ll` を実行。証跡: `reports/bandit_2026-Q2.txt`

### High（修正済）

| ルール | 場所 | 内容 | 対応 |
| :--- | :--- | :--- | :--- |
| B324 (CWE-327) | `scripts/sync_wbs_to_calendar.py:628` | Calendar イベント重複排除用 syncKey 生成に SHA1 を使用 | 非セキュリティ用途（同一性キー）のため `usedforsecurity=False` を付与し本セッションで修正。再スキャンで High 0 件を確認 |

### Medium（未解決 → R50 / T802）

| ルール | 件数 | 場所 | 対応方針 |
| :--- | :--- | :--- | :--- |
| B113 requests timeout 未指定 (CWE-400) | 17 | `scripts/sync_wbs_to_calendar.py`(10) / `scripts/share_resources.py`(4) / `scripts/create_recurrent_regular_review.py`(3) | Google API 呼び出しへ `timeout=30` を一括付与。sync スクリプトは Codex レーン管轄のため T802 で対応（SLA: 1 週間以内） |
| B310 urlopen scheme 監査 (CWE-22) | 1 | `scripts/verify_public_demo.py:62` | **受容**: URL は固定の https 公開デモ URL（CLI 引数も運用上ガード対象 URL のみ）。スキーム固定のため悪用経路なし |
| B108 hardcoded /tmp (CWE-377) | 2 | `src/app.py:269,279` | **受容**: Cloud Functions / Cloud Run のサーバーレス実行環境では `/tmp` が唯一の書込可能領域であり意図した設計（SQLite fallback 用）。マルチテナント共有 /tmp ではない |

Low 24 件は四半期レビュー対象として次回監査（2026-Q3）で棚卸しする。

### 未実施

- Semgrep（OWASP ルールセット）: Windows ローカルでの実行制約のため未実施。次回監査までに CI（GitHub Actions ubuntu ランナー）への組み込みを検討（ランブック §7）。
- ESLint security plugin: ルートに `package.json` が存在せず、フロントエンドは静的 HTML（CDN script は SRI 済 / SEC-002）のため対象外と判定。

## 2. 依存ライブラリ脆弱性（pip-audit）

`pip-audit -r requirements.txt` を実行。証跡: `reports/pip_audit_2026-Q2.json`（88 パッケージ照合）

| パッケージ | CVE | 内容 | 修正版 | 対応 |
| :--- | :--- | :--- | :--- | :--- |
| starlette 0.52.1（fastapi 0.136.3 の推移的依存） | CVE-2026-48710 / PYSEC-2026-161 / GHSA-86qp-5c8j-p5mr | Host ヘッダ未検証により `request.url.path` が実ルーティングパスと乖離し、`request.url` ベースのパス認可がバイパスされ得る | 1.0.1 | **R49 / T802**: 本アプリの Basic Auth は FastAPI `Depends(HTTPBasic)`（エンドポイント単位）と `BasicAuthStaticFiles`（mount scope 単位）で、`request.url.path` ベースの認可ミドルウェアは不使用 — 直接悪用経路は確認されず。ただし防御多層化のため starlette ≥1.0.1 へ更新し、fastapi 対応範囲の確認と `requirements.txt` への下限ピン追加を SLA 1 週間内に実施 |

npm audit: ルート `package.json` なしのため対象外。

## 3. Supabase RLS ポリシー検証

`pytest tests/test_rls_policies.py -v` → **3 件全パス**。`supabase/migrations/20260606000000_init_schema.sql` をチェックリスト照合:

- [x] 全 4 テーブル（profiles / matches / audits / usage_ledgers）で `ENABLE ROW LEVEL SECURITY` 設定済
- [x] profiles: SELECT / UPDATE / INSERT に所有者ポリシーあり、**DELETE ポリシーなし**（フロントからの直接削除禁止 — 退会は T742 の Cloud Functions 経由フローのみ）
- [x] `public.firebase_uid() = user_id` の所有者チェック実装済（JWT `sub` クレーム参照、改変可能な `user_metadata` 不使用）
- [x] audits / usage_ledgers の書込ポリシーなし → Service Role Key（Cloud Functions 限定）のみ書込可能
- [x] anon ロールは全個人情報テーブルへアクセス不可（RLS デフォルト拒否）
- [x] アプリ `init_db` 作成テーブル（engineers / jobs / match_results）は T795（2026-06-11）で RLS 有効化済 — anon REST 露出遮断を本番確認済

## 4. シークレット漏洩検知

- パターンスキャン（Google API key / Supabase JWT / OpenAI key / 秘密鍵 PEM / Slack token / Stripe live key / webhook secret）: ヒット 1 件 → `credentials.json.template` のプレースホルダー（`YOUR_PRIVATE_KEY_HERE`）で**誤検知**。実シークレットの混入なし
- git 追跡確認: `client_secret.json` / `credentials.json` / `authorized_user.json` / `.env` / `.claude/settings.local.json` / `CLAUDE.local.md` はすべて未追跡かつ `.gitignore` で ignore 済を `git check-ignore` で確認
- truffleHog / gitleaks による Git 全履歴スキャン: ローカル未導入のため未実施。CI への gitleaks 組み込み（ランブック §7、SHA ピン留め）を T747（Dependabot 設定）と合わせて Codex レーンで検討

## 検出事項と対応状況

| ID | 重要度 | 内容 | 状態 | 期限 |
| :--- | :--- | :--- | :--- | :--- |
| SEC-004 | HIGH | B324: SHA1 syncKey（非セキュリティ用途） | **修正済**（2026-06-12、`usedforsecurity=False`） | — |
| SEC-005 (R49) | HIGH | starlette CVE-2026-48710 → ≥1.0.1 へ更新 | OPEN → T802（Codex） | 2026-06-19 |
| SEC-006 (R50) | MED | B113: requests timeout 未指定 17 箇所 | OPEN → T802（Codex） | 2026-06-19 |
| SEC-007 | LOW | B310 / B108 | 受容（理由は §1） | — |

## 次回監査予定: 2026-09（2026-Q3 / 第 2 回）

持ち越し事項: Semgrep・gitleaks の CI 組み込み、Bandit Low 24 件の棚卸し、外部ペネトレーションテスト（T805）結果の反映。
