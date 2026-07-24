# 適性・状況診断アンケート UAT検証完了レポート

- **検証対象機能**: 社内向け適性・状況診断アンケート / 適性・モチベーション自己診断デモ
- **実施日**: 2026-07-24
- **検証責任者**: Antigravity (適性アンケート担当)
- **対象ケース**: TS-01, TS-21, TS-43
- **判定結果**: ✅ **全ケース OK / PASS (ドリフト0)**

---

## 1. 検証結果サマリ

| テストID | テストケース名 | 関連WBS / 課題 | 実行テスト数 | 判定 |
| :--- | :--- | :--- | :---: | :---: |
| **TS-01** | 適性アンケートの同意必須送信 | T840, T883 / R98, R126 | 6 | ✅ OK |
| **TS-21** | 適性・状態自己診断デモ（要配慮個人情報の非永続） | T876, T876_1 / R119, QA-105 | 9 | ✅ OK |
| **TS-43** | 自己診断の評価基準点（正常/注意/面談目安）とフィードバック面談メモ | T909 / R148, QA-105 | 17 | ✅ OK |
| **監査・カバレッジ** | UAT仕様書整合性 & UAT-API逆トレーサビリティ監査 | T882, T892 / QA-111, R136 | 12 | ✅ OK |

---

## 2. ケース別詳細検証結果

### TS-01: 適性アンケートの同意必須送信 (T840 / T883)
- **検証API**: `POST /api/employee-assessment/responses`
- **検証項目**:
  1. **同意チェックなし送信ブロック**: 同意以外の必須項目（社内確認コード・部署・10文字以上のフリー記述）を入力し、同意なしの状態でブラウザおよびサーバーが保存を拒否することを確認。
  2. **正常保存**: 全項目＋同意ありで `response_id` が返却されることを確認。
  3. **エラーメッセージ具体性**: フリー記述9文字以下のサーバーHTTP 400エラー時に「接続できませんでした」等の隠蔽表示にならず「フリー記述は10文字以上で入力してください」の具体的理由が日本語表示されることを確認（T883 / R126の回帰防止）。
- **機械検証**: `tests/test_survey_error_handling.py` (6 passed)

### TS-21: 適性・状態自己診断デモ（要配慮個人情報の非永続） (T876)
- **検証API**: `POST /api/aptitude-demo/questions`, `POST /api/aptitude-demo/evaluate`
- **検証項目**:
  1. **同意必須**: 同意チェックなしでの評価要求に対して HTTP 400（`consent is required before running the self-check evaluation`）で拒否されることを確認。
  2. **DB非依存構造**: バックエンドモジュール `src/aptitude_demo.py` が DB・永続ストレージを一切 `import` しない構造的非保存設計であることを検証。
  3. **監査ログ個人情報非蓄積**: 監査ログ（`ai_audit.jsonl`）に診断スコア・回答値・面談メモが保存されず、`answered_count` 件数のみが記録されることを実機確認。
- **機械検証**: `tests/test_aptitude_demo_frontend.py` (11 passed)

### TS-43: 自己診断の評価基準点とフィードバック面談メモ (T909)
- **検証API**: `GET /api/aptitude-demo/legend`, `POST /api/aptitude-demo/evaluate`
- **検証項目**:
  1. **評価基準点の単一正本管理**: サーバ `src/aptitude_demo.py` の `SCORE_BANDS` から **面談目安 (0〜49.9)** / **注意 (50〜74.9)** / **正常 (75〜100)** の3段階が隙間・重複なく提示されることを確認。
  2. **凡例APIと判定の一致**: `GET /api/aptitude-demo/legend` が評価前にも同じ3段階基準を返却し、画面UI凡例と判定表示が一致することを確認。
  3. **月次フィードバック面談メモ**: スコア評価時に最も低い項目（最弱要素）に対応する会話切り出し文・10〜20分目安の問いかけ・次アクション・注意書きが安全に生成されることを確認。
  4. **非医療・非人事評価免責**: 面談メモに「人事評価・処遇判断の材料には使用しません」「医療的判断を行わない」旨の注記が明記され、不利益取扱いを防止する文言設計であることを確認。
  5. **単独共有導線**: `#aptitude-demo-standalone` ハッシュ導線で自己診断セクションのみが単独表示され、不要セクションが安全に隠蔽されることを確認。
- **機械検証**: `tests/test_aptitude_score_bands.py` (17 passed)

---

## 3. テスト実行証跡

```powershell
python -m pytest tests/test_survey_error_handling.py tests/test_aptitude_demo_frontend.py tests/test_aptitude_score_bands.py tests/test_verify_supabase_uat_writes.py -v
```

**結果**: 35 passed in 4.22s

```powershell
python -X utf8 scripts/audit_uat_test_spec.py
python -X utf8 scripts/audit_uat_api_coverage.py
```

**結果**: 監査結果 ✅ PASS (43/43 UATケース網羅・APIカバレッジ100%・ドリフト0)

---

## 4. 結論

適性アンケート担当として、社内向け適性・状況診断アンケート（TS-01）、要配慮個人情報の非永続設計（TS-21）、および評価基準点・フィードバック面談活用メモ（TS-43）の全ての仕様・UI・API・プライバシー保護策についてUAT検証を完遂し、✅ **合格 (PASS)** を宣言します。
