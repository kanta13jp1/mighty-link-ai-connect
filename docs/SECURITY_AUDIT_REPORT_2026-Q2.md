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
| 静的解析 (Bandit 1.9.4) | ✅ PASS（T802 で修正完了） | High 0 / Medium 0 / Low 24 | 0 件 |
| 依存ライブラリ脆弱性 (pip-audit 2.10.1) | ✅ PASS（T802 で修正完了） | 0 件 | 0 件 |
| RLS ポリシー検証 (pytest + SQL レビュー) | ✅ PASS | 0 件 | 0 件 |
| シークレット漏洩 (パターンスキャン + git 追跡確認) | ✅ PASS | 0 件（誤検知 1 件のみ） | 0 件 |
| 外部ペネトレーション疑似診断 (T805) | ⚠️ WARNING | High 0 / Medium 4 / Low 7 | R94 |

**総合判定**: PASS（controlled demo） / WARNING（public paid launch） — High 検出は監査セッション内で修正完了し、未解決だった R49（starlette CVE）/ R50（requests timeout）/ R52（FastAPI startup deprecated）も T802 で修正完了。2026-06-13 の再スキャンで Bandit High/Medium 0 件、pip-audit 0 件、pytest 21 件通過を確認した。2026-06-21 の T805 疑似診断では High 0 / secret-like値露出 0 を確認したが、CSP / X-Content-Type-Options 等の公開URLヘッダhardeningを R94 / T835 へ継続する。

---

## 1. 静的解析（Bandit）

`bandit -r src/ scripts/ main.py -ll` を実行。証跡: `reports/bandit_2026-Q2.txt`（2026-06-13 再生成）

### High（修正済）

| ルール | 場所 | 内容 | 対応 |
| :--- | :--- | :--- | :--- |
| B324 (CWE-327) | `scripts/sync_wbs_to_calendar.py:628` | Calendar イベント重複排除用 syncKey 生成に SHA1 を使用 | 非セキュリティ用途（同一性キー）のため `usedforsecurity=False` を付与し本セッションで修正。再スキャンで High 0 件を確認 |

### Medium（T802 で修正済）

| ルール | 件数 | 場所 | 対応 |
| :--- | :--- | :--- | :--- |
| B113 requests timeout 未指定 (CWE-400) | 17 | `scripts/sync_wbs_to_calendar.py`(10) / `scripts/share_resources.py`(4) / `scripts/create_recurrent_regular_review.py`(3) | Google API 呼び出しへ `timeout=30` を一括付与し、再スキャンで Medium 0 件を確認 |
| B310 urlopen scheme 監査 (CWE-22) | 1 | `scripts/verify_public_demo.py` | `urllib.request.urlopen` を `requests.get(..., timeout=30)` へ置換し、公開デモ guard の挙動を維持したまま解消 |
| B108 hardcoded /tmp (CWE-377) | 2 | `src/app.py` | SQLite fallback の一時 DB パスを `tempfile.gettempdir()` 経由に変更し、サーバーレス書込先の意図を保ったまま解消 |

Low 24 件は四半期レビュー対象として次回監査（2026-Q3）で棚卸しする。

### 未実施

- Semgrep（OWASP ルールセット）: Windows ローカルでの実行制約のため未実施。次回監査までに CI（GitHub Actions ubuntu ランナー）への組み込みを検討（ランブック §7）。
- ESLint security plugin: ルートに `package.json` が存在せず、フロントエンドは静的 HTML（CDN script は SRI 済 / SEC-002）のため対象外と判定。

## 2. 依存ライブラリ脆弱性（pip-audit）

`pip-audit -r requirements.txt` を実行。証跡: `reports/pip_audit_2026-Q2.json`（2026-06-13 再生成）

| パッケージ | CVE | 内容 | 修正版 | 対応 |
| :--- | :--- | :--- | :--- | :--- |
| starlette 0.52.1（旧環境の推移的依存） | CVE-2026-48710 / PYSEC-2026-161 / GHSA-86qp-5c8j-p5mr | Host ヘッダ未検証により `request.url.path` が実ルーティングパスと乖離し、`request.url` ベースのパス認可がバイパスされ得る | 1.0.1 | **修正済 (R49 / T802)**: `requirements.txt` に `fastapi>=0.136.3` と `starlette>=1.0.1,<1.1.0` を追加。再スキャンで既知脆弱性 0 件を確認 |

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
- truffleHog / gitleaks による Git 全履歴スキャン: ローカル未導入のため未実施。T747では新規サードパーティ action を増やさず、Dependabot と週次 Bandit / pip-audit を先行導入。Git 全履歴のシークレットスキャンは、SHAピン留めまたはローカルCLI実行方針を決めたうえで次回監査/外部診断時に扱う。

## 5. 外部ペネトレーション疑似診断（T805）

`python scripts/run_external_pentest_review.py --timeout 15` を実行し、[EXTERNAL_PENTEST_RUNBOOK.md](EXTERNAL_PENTEST_RUNBOOK.md) と `exports/external_pentest_review.*` に証跡を保存した。

| 対象 | 到達 | High | Medium | Low | 主要メモ |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `https://kanta13jp1.github.io/mighty-link-ai-connect/` | 200 | 0 | 2 | 5 | CSP / X-Content-Type-Options 不足、CORS wildcard、Clickjacking/Referrer/Permissionsヘッダ不足 |
| `https://mightylink-app.com/` | 200 | 0 | 2 | 4 | CSP / X-Content-Type-Options 不足、Clickjacking/Referrer/Permissionsヘッダ不足 |

機微パス（`.env`、`.git/config`、OAuth/credentials系ファイル、Claudeローカル設定）の限定プローブは 14 件実施し、secret-like値露出は 0 件だった。

## 検出事項と対応状況

| ID | 重要度 | 内容 | 状態 | 期限 |
| :--- | :--- | :--- | :--- | :--- |
| SEC-004 | HIGH | B324: SHA1 syncKey（非セキュリティ用途） | **修正済**（2026-06-12、`usedforsecurity=False`） | — |
| SEC-005 (R49) | HIGH | starlette CVE-2026-48710 → ≥1.0.1 へ更新 | **修正済**（T802、2026-06-13） | — |
| SEC-006 (R50) | MED | B113: requests timeout 未指定 17 箇所 | **修正済**（T802、2026-06-13） | — |
| SEC-007 | LOW | B310 / B108 | **修正済**（T802、2026-06-13） | — |
| SEC-008 (R94) | MED | 公開URLの CSP / X-Content-Type-Options 等のヘッダhardening不足 | **継続**（T835、2026-06-25予定） | 2026-06-25 |

## 次回監査予定: 2026-09（2026-Q3 / 第 2 回）

持ち越し事項: Semgrep・gitleaks の CI 組み込み、Bandit Low 24 件の棚卸し、T835 の公開URLヘッダhardening完了確認。
