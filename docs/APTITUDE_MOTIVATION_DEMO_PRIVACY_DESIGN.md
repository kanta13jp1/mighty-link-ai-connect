# 適性・モチベーション自己診断デモ プライバシー設計（T876）

- 作成日: 2026-07-08
- 対象WBS: T876（法務配慮プロトタイプ）/ 実装: T876_1（Claude Codeレーン巻き取り）
- 関連課題/QA: R119（精神状態評価AIの法務・プライバシーリスク）/ QA-105（要配慮個人情報の安全な取り扱い境界）
- 実装: `src/aptitude_demo.py`（純ロジック）/ `src/app.py`（API）/ テスト: `tests/test_aptitude_demo.py`（10仮説・13件）
- 由来: 2026-07-08 CEO定例で「AIで精神状態を可視化するアンケート設問生成」の要望

## 1. 位置づけと法的前提

本機能は**体験用プロトタイプ**である。従業員の精神状態・モチベーションに関する回答および算出スコアは、日本の個人情報保護法上の**要配慮個人情報**に該当し得る。労務管理における不利益利用の懸念もあるため（R119）、本運用化の前に法務・プライバシー規約の更新を別途要する。プロトタイプ段階では、**要配慮個人情報を蓄積しない**ことを設計の中心に据える。

## 2. DB非保存の「構造的」担保

「保存しない運用」ではなく「保存できない構造」で担保する。

- ロジックは独立モジュール `src/aptitude_demo.py` に分離し、**DB接続・Supabase・SQLite・ストレージヘルパーを一切importしない**。回答をストレージへ書き込むコードパスが存在しない（テスト `test_h4_module_has_no_storage_imports` で `psycopg2/sqlite3/get_db_connection/supabase/INSERT/cursor` の非出現を固定）。
- APIエンドポイント（`/api/aptitude-demo/questions`、`/api/aptitude-demo/evaluate`）は純関数を呼ぶだけで、`db_insert_*` を一切呼ばない。評価を繰り返しても保存系テーブル（例: feedback_events）の行数が増えないことをテストで確認（`test_h4_evaluation_creates_no_db_rows`）。
- 回答値と算出スコアは**リクエストのメモリ内でのみ**存在し、レスポンス返却後は破棄される（ステートレス。サーバーにセッション状態を持たない）。

## 3. 監査ログの最小化

- 監査ログには「質問生成が行われた（件数・source・persisted=false）」「評価が行われた（回答件数・persisted=false・answers_stored=false・score_stored=false）」のみを記録する。
- **個々の回答値・次元別スコア・総合スコア・condition_indexは監査ログに残さない**（`test_h5_audit_log_excludes_answers_and_score` で `overall_score/condition_index/dimension_scores` の非出現を固定）。

## 4. 設問の安全設計

- 設問は精神状態を**直接**問わず、間接指標（エネルギー/集中/業務量/回復・休息/対人関係/やりがい）を5段階で自己申告する肯定文とする。
- AI生成設問は安全フィルタ（`SENSITIVE_DIRECT_PATTERNS`）を通し、病名・診断・服薬・通院・自傷・休職・ハラスメント等の要配慮/医療的トピックを直接尋ねる設問を除外する。除外分は検証済みの固定設問セット（20問）から補填するため、AIが不適切な設問を返しても最終出力は常に安全（`test_h6` / `test_h9_gemini_success_is_sanitized`）。
- Gemini未設定・API失敗時は固定設問セットにフォールバックし、デモは常に動作する。

## 5. 同意と免責

- 質問取得・評価の両APIで利用規約・プライバシーポリシー同意を必須とし、評価APIは追加の明示同意（`consented`）も必須とする（未同意は400）。
- レスポンスに保存しない旨の`privacy_notice`を常に含める。評価結果には「医療的診断ではない」旨の`disclaimer`を含める。

## 6. 本運用に向けた残論点（プロトタイプでは対象外）

- 要配慮個人情報を保存・分析する場合の取得同意・利用目的特定・保管期間・アクセス制御・不利益取扱い禁止の規約整備（法務レビュー）。
- 保存する場合のRLS・匿名化・保持/削除（[DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md)への追記）。
- フロントエンドUI（画面のみで完結する回答フォーム・結果表示）はAntigravityレーンで実装（T876本体）。本APIはブラウザメモリ内で完結する前提の契約（persisted=false）を提供する。

## 7. 検証コマンド

```powershell
python -m pytest tests/test_aptitude_demo.py -q
```
