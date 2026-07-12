# 🔗 ドキュメント参照整合性ガード (T891)

> `docs/` 配下の全 Markdown が、**壊れたリンク・機種依存の絶対パス・リポジトリ外への参照**を持たないことを、**人間が手順どおり実行して OK/NG を判断できる**ように定義したガード仕様書。
>
> docs は3レーン（Antigravity / Codex / Claude Code）が書き足す大規模ナレッジベースで、リンク切れ・`file:///c:/Users/...` の絶対パス・`~/.claude` メモリ等リポジトリ外への参照が混じると、docs が信頼できなくなり、**陳腐化 doc の安全な削除も阻害する**（何がそのファイルを参照しているか分からない）。本ガードはそれを CI で落とす。

---

## 1. 目的

- docs 内の全リンクが**移植可能な repo-relative 参照**で、かつ**実在ファイルに解決**することを保証する。
- 将来の陳腐化 doc 削除を安全化する（削除対象を参照する doc が残っていれば本ガードが落ちる）。

## 2. 実行方法

```powershell
python scripts/audit_docs_reference_integrity.py
python -m pytest tests/test_docs_reference_integrity.py -q
```

監査は `exports/docs_reference_integrity_audit.{json,md}` に結果を出力し、10仮説すべて PASS で終了コード 0、1つでも FAIL で 1 を返す。

## 3. 10仮説（人間が確認できる観点）

| 仮説 | 内容 | OK と言える条件 |
| :-- | :-- | :-- |
| H1 | 走査対象 | docs が50件以上あり、内部リンク（http/mailto以外）を1件以上検出 |
| H2 | 非移植パス排除 | `file:///` 絶対パスのリンクが0件 |
| H3 | リポジトリ外参照排除 | リポジトリ外（`~/.claude` 等）を指すリンクが0件 |
| H4 | docs→docs | `*.md` への相対リンクがすべて実在に解決 |
| H5 | docs→コード | `scripts/*.py`・`tests/*.py` へのリンクがすべて実在 |
| H6 | docs→データ | `data/*.tsv`・`exports/*` へのリンクがすべて実在 |
| H7 | docs→その他 | `src/`・config 等その他 repo 内リンクがすべて実在 |
| H8 | アンカー付き | `file.md#section` 形式のファイル部分が実在 |
| H9 | 未解決0 | repo-relative リンクの未解決が合計0件 |
| H10 | 全体整合 | H1〜H9 がすべて PASS（リンクドリフト0） |

## 4. 判定

- **OK**: `python scripts/audit_docs_reference_integrity.py` が「総合判定: ✅ PASS」を表示し、`tests/test_docs_reference_integrity.py` が全件 green。
- **NG**: いずれかの仮説が ❌。監査出力の「詳細」列に、`file:///` リンク・外部リンク・未解決リンク（doc/code/data/other 別）・未解決アンカーが具体的に列挙される。

## 5. NG 時の対応

1. **H2 `file:///`**: 機種依存の絶対パスを **repo-relative**（docs 内からは `../data/...`、同ディレクトリの doc は `NAME.md`）に直す。
2. **H3 外部参照**: `~/.claude` 等リポジトリ外のファイルへのリンクは**リンクを外す**（インラインコード等の素テキストにする）。メモリはリポジトリに含めない。
3. **H4〜H8 リンク切れ**: 参照先を実在パスに修正、またはファイルを追加/復活させる。doc を削除する場合は、本ガードで**その doc を参照する箇所が残っていない**ことを確認してから削除する。
4. 修正後に監査とテストを再実行し 10/10 PASS を確認してからコミット。

## 6. 補足

- 本ガードは docs 内の**リンク解決**を保証する。トラッカーが参照するファイルの整合は [TRACKER_INTEGRITY_GUARD.md](TRACKER_INTEGRITY_GUARD.md)（T890）、WBS 工程網羅は [WBS_LIFECYCLE_COVERAGE_GUARD.md](WBS_LIFECYCLE_COVERAGE_GUARD.md)（T889）が担保する。
- 初回整備（T891）で `file:///` 10件・repo外/リンク切れ11件（計21件・9docs）を検出・修正した。
