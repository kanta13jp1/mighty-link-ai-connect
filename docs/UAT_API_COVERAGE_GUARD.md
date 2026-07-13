# 🎯 UAT-API網羅トレーサビリティガード (T892)

> `src/app.py` の全 API エンドポイントが、**GA ユーザー向けなら必ず人間実行可能な UAT ケースを持ち**、内部/デバッグ/デモ/gated なものは**理由付きで対象外**に分類されていることを、**人間が手順どおり実行して OK/NG を判断できる**ように定義したガード仕様書。
>
> `scripts/audit_uat_test_spec.py`（T882）は「UAT が挙げた API が実在するか」＝**forward** を検証する。本ガードは、テストファーストに必要な **reverse**（＝出荷済みのユーザー向けエンドポイントに UAT が存在するか、新規エンドポイントが未分類のまま出荷されていないか）を CI で検証する。

---

## 1. 目的

- GA ユーザー向けエンドポイントの**受入テスト網羅**を保証する（テストファーストの網羅性）。
- 新規エンドポイント追加時に**分類（REQUIRED / EXEMPT）の判断を強制**し、無言の未検証出荷を防ぐ。

## 2. 分類方針

| 区分 | 意味 | UAT |
| :-- | :-- | :-- |
| **REQUIRED_GA** | GA のユーザー向け機能面（診断/勤怠/営業メール/管理者/同意/エクスポート/サポート/フィードバック/適性デモ 等） | **必須** |
| **EXEMPT** | 内部・デバッグ・デモ・gated（Seedance 凍結、Stripe 有償化前、利用量台帳、比較ボード用データ取得等）。各エントリに理由を明記 | 不要 |

分類は `scripts/audit_uat_api_coverage.py` の `REQUIRED_GA_ENDPOINTS` / `EXEMPT_ENDPOINTS` に定義する。`/api/` 契約面のみ対象（ページ/静的ルートは範囲外）。

## 3. 実行方法

```powershell
python scripts/audit_uat_api_coverage.py
python -m pytest tests/test_uat_api_coverage.py -q
```

監査は `exports/uat_api_coverage_audit.{json,md}` に結果を出力し、10仮説すべて PASS で終了コード 0、1つでも FAIL で 1 を返す。

## 4. 10仮説（人間が確認できる観点）

| 仮説 | 内容 | OK と言える条件 |
| :-- | :-- | :-- |
| H1 | 走査 sanity | `/api/` エンドポイント30件以上・UATケース20件以上 |
| H2 | forward 整合 | UAT が挙げる全 API が `src/app.py` に実在 |
| H3 | reverse 被覆 | 全 REQUIRED_GA エンドポイントが UAT ケースで被覆 |
| H4 | 分類網羅 | 全 `/api/` エンドポイントが REQUIRED ∪ EXEMPT に分類済み（未分類0） |
| H5 | 二重分類なし | REQUIRED ∩ EXEMPT = ∅ |
| H6 | stale required なし | 全 REQUIRED が `src/app.py` に実在 |
| H7 | stale exempt なし | 全 EXEMPT が `src/app.py` に実在 |
| H8 | 中核ドメイン被覆 | 診断/勤怠/営業メール/管理者/サポート/フィードバック/エクスポートが各≥1被覆 |
| H9 | 被覆率 | REQUIRED カバレッジ率 = 100% |
| H10 | 全体整合 | H1〜H9 がすべて PASS（トレーサビリティドリフト0） |

## 5. 判定

- **OK**: `python scripts/audit_uat_api_coverage.py` が「総合判定: ✅ PASS」を表示し、`tests/test_uat_api_coverage.py` が全件 green。
- **NG**: いずれかの仮説が ❌。詳細列に、未被覆 REQUIRED・未分類エンドポイント・stale・未被覆ドメインが列挙される。

## 6. NG 時の対応

1. **H4 未分類**（新規エンドポイント追加時に最頻）: そのエンドポイントを REQUIRED か EXEMPT に分類する。ユーザー向けなら REQUIRED に入れて `docs/UAT_TEST_SPECIFICATION.md` に UAT ケースを追加（テストファースト）。内部等なら EXEMPT に理由付きで追加。
2. **H3/H9 未被覆**: `docs/UAT_TEST_SPECIFICATION.md` に該当 UAT ケースを追加する。
3. **H6/H7 stale**: 削除・改名されたエンドポイントを分類集合から除く。
4. 修正後に本監査と `tests/test_uat_api_coverage.py`・`tests/test_uat_test_spec.py` を再実行し 10/10 PASS を確認してからコミット。

## 7. 補足

- 初回整備（T892）で、GA ユーザー向けだが UAT 未整備だった **適性診断デモ（TS-21）** と **営業メール解析統計（TS-22）** のケースを追加し、REQUIRED 被覆を 100% にした。
- 本ガードは UAT の**存在網羅**を保証する。各ケースの**手順の妥当性**（人間が OK/NG 判断できる詳細さ）は [UAT_TEST_SPECIFICATION.md](UAT_TEST_SPECIFICATION.md) と `audit_uat_test_spec.py`（T882）が担保する。
