# 🚦 レーン・プリフライトガード (T894)

> 3レーン（Antigravity / Codex / Claude Code）のローカル作業を軽量に保ちつつ、GitHub-hosted Actions で **全整合ガード・全自動テスト・Playwright Chromium がgreen** であることを exact SHA 単位で強制するガード仕様書。
>
> 既存の `scripts/audit_*.py` 群（16件）は「各ドメインの整合」を個別に守る。本ガードはその**上位**で、「**レーンがredの作業ツリーを出荷できない**」ことを守る。

---

## 1. 背景（なぜ必要か）

2026-07-16 のセッション開始時、作業ツリーに他レーン由来の未コミット変更があり、`docs/UAT_TEST_SPECIFICATION.md` から **TS-11 / TS-12 が削除され TS-13 の本文が TS-11 見出しの下に取り残される**破損が混入していた。結果、`pytest tests/` は **3 failed / 455 passed** の red だった（R123）。

この破損自体は既存ガード（T882 / T892）が検知できる。問題は**検知が走る場所**だった:

- `AGENTS.md` の「Required Session Closeout」には **`pytest` も `audit_*.py` も含まれていない**。生成・同期スクリプトのみ。
- したがって手順どおりに作業したレーンでも、**red のままコミット・push し、main CI で初めて落ちる**。
- 公式ガイダンスとも乖離していた:
  - Anthropic Claude Code Docs（memory / hooks）: 「CLAUDE.md は context であって強制ではない。**commit 前など特定タイミングで必ず走らせたい処理は hook にせよ**」
  - OpenAI Codex Docs（AGENTS.md / best practices）: 「AGENTS.md には**検証コマンドと完了条件**を書く」「commit 前に**ビルド・テストの成功を必須にする**」

本ガードはこの乖離を埋め、**「16ガード＋全テストの一括実行」を1コマンド化**して closeout の先頭に置く。

## 2. 目的

- ローカルは高速ガードと変更範囲の静的/targeted test に限定し、重い全テストとブラウザテストは GitHub-hosted Actions を主実行場所にする。
- レーンが **red の作業ツリーをコミットしない**ことを高速ガードで保証し、red / 未検証の候補 SHA を `main` / `master` に昇格しない。
- 新規ガード追加時に**分類の判断を強制**し、ガードの無言スキップを防ぐ。
- 各ガードが**CI 実行経路（pytest から到達可能）を持つ**ことを保証する。ガードは「書いたが CI で走っていない」と無価値になるため。
- 成否にかかわらず JSON / Markdown / JUnit XML / pytest log を短期 artifact として残し、ローカル再実行なしで失敗件数と詳細を診断できるようにする。

## 2.1 分類方針（T892 の REQUIRED / EXEMPT と同じ考え方）

| 区分 | 意味 | プリフライト |
| :-- | :-- | :-- |
| **GUARD_REGISTRY** | リポジトリ整合ガード。作業ツリーの正しさを判定する | **実行必須**（PASS・CI経路・証跡出力を要求） |
| **EXEMPT_GUARDS** | 整合ガードではない運用ツール。理由を明記 | 対象外（コミットをブロックしない） |

分類は `scripts/run_lane_preflight.py` の 2 つの辞書に定義する。現時点の対象外は 1 件のみ:

- `audit_external_api_usage.py` — 運用日次ツール（T736）。正本が **gitignore のローカル台帳** `data/external_api_usage.jsonl` で、レポート先も `reports/`。作業ツリーの整合とは無関係なため、これでコミットをブロックするのは誤り。

## 3. 実行方法

```powershell
# 高速モード（整合ガードのみ・数秒）: ローカルのコミット直前
python scripts/run_lane_preflight.py

# 完全モード: GitHub Actions「Cloud Full Preflight」の正規実行コマンド
python scripts/run_lane_preflight.py --full

# 本ガード自体の自己検証
python -m pytest tests/test_lane_preflight.py -q
```

結果は `exports/lane_preflight_report.{json,md}` に出力し、完全モードではさらに `exports/lane_preflight_pytest.xml` と `exports/lane_preflight_pytest.log` を永続化する。10仮説すべて PASS で終了コード 0、1つでも FAIL で 1 を返す。JUnit XMLを件数の正本としてpytestのバージョンやsummary文言に依存しない。

ローカル `--full` は GitHub Actions が利用不能な場合、またはユーザーが明示的に要求した場合だけのfallbackとする。通常は `codex/preflight-*` または `codex/preflight/<task>` の隔離候補ブランチへcommit/pushし、`.github/workflows/cloud-preflight.yml` の同一 SHA 実行を待つ。workflowはrepository secretsを受け取らず、permissionsは`contents: read`だけである。

Windowsでは親ランナーと子ガードの入出力をUTF-8へ固定する。日本語と判定記号を含む出力がCP932で例外終了し、ガード本体のPASSをFAILと誤認しないこともプリフライト自身の回帰テストで固定する。

## 4. 10仮説（人間が確認できる観点）

| 仮説 | 内容 | OK と言える条件 |
| :-- | :-- | :-- |
| H1 | 走査 sanity | 対象ガード10件以上・テストファイル50件以上を検出 |
| H2 | 分類網羅 | `scripts/audit_*.py` が全て `GUARD_REGISTRY` ∪ `EXEMPT_GUARDS` に分類済み（未分類0） |
| H3 | stale 分類なし | 分類済みガードが全て実在（削除・改名の取り残し0） |
| H4 | 全ガード PASS | 対象ガードの実行終了コードが全て 0 |
| H5 | テスト失敗0 | `--full` 時、`pytest tests/` の failed / error が 0 |
| H6 | テスト規模 sanity | `--full` 時、収集テストが400件以上（テストスイートの無言縮退検知） |
| H7 | CI 実行経路 | 全対象ガードが `tests/` の**いずれかのテストから import** されている |
| H8 | 証跡出力 | 全対象ガードが**自身のソースで宣言したとおり**の `exports/*.md` を出力済み |
| H9 | 手順ドリフト0 | `AGENTS.md` の closeout に本プリフライトコマンドが記載されている |
| H10 | 全体整合 | H1〜H9 がすべて PASS（プリフライトドリフト0） |

> **H5 / H6 の注記**: 高速モード（`--full` なし）ではテストを実行しないため、H5/H6 は `skipped=true` として **PASS 扱い**とし、`詳細`列に「高速モード（未実行）」と明示する。push後、候補SHAのCloud Full Preflight成功が昇格条件になる。

## 5. 判定

- **OK**: 候補ブランチの exact SHA に対する Cloud Full Preflight が「総合判定: ✅ PASS」を表示し、終了コード 0 で完了し、artifactに証跡がある。
- **NG**: いずれかの仮説が ❌。詳細列に、未登録ガード・stale 登録・FAIL したガード名・pytest の failed 件数・import されていないガード・証跡欠落・AGENTS.md の記載欠落が具体的に列挙される。

## 6. NG 時の対応

1. **H2 未分類**（新規ガード追加時に最頻）: 追加した `scripts/audit_*.py` を `run_lane_preflight.py` の `GUARD_REGISTRY`（目的を1行添える）か `EXEMPT_GUARDS`（対象外の理由を明記）へ分類する。
2. **H3 stale**: 削除・改名したガードを分類辞書から除く。
3. **H4 ガード FAIL**: 該当ガードを単体実行し、そのガード仕様書の「NG 時の対応」に従う。**プリフライトを迂回してコミットしない**。
4. **H5 テスト失敗**: Cloud artifactのJUnit XMLとpytest logで失敗テストを特定して修正する。ローカルで全suiteを再実行する必要はない。他レーンの未コミット変更が原因の場合は、**破損を勝手に捨てず**バックアップを取ってから当該レーンへ差し戻す（R123 の対応を踏襲）。
5. **H7 import なし**: そのガードの `evaluate()` を検証する `tests/test_*.py` を追加する（テストファースト）。
6. **H9 手順ドリフト**: `AGENTS.md` の closeout に本コマンドを戻す。

## 7. 適用手順（3レーン共通）

| タイミング | コマンド | 目的 |
| :-- | :-- | :-- |
| ローカル・コミット直前 | `python scripts/run_lane_preflight.py` + 変更範囲のtargeted test/static check | 数秒。整合ドリフトの混入を防ぐ |
| 候補ブランチpush後 | GitHub Actions: `python scripts/run_lane_preflight.py --full` | GitHub-hostedで全suite/ブラウザを検証しartifact化 |
| `main` / `master` 昇格前 | Actions成功SHAと候補SHAの完全一致を確認 | 未検証・red・cancelled・別SHAの昇格を禁止 |

`main` / `master` への昇格は、Cloud Full Preflightが成功した**そのSHAだけ**をnon-forceかつfast-forwardで行う。remote refが想定から動いた場合は停止し、新しい候補SHAとして再検証する。redのmain/masterを作らない。sales-email-syncのfail-closedテストや既存ガードは緩和・除外しない。

## 8. 補足・範囲外

- 本ガードは**実行の集約と網羅**を保証する。各ドメインの判定ロジックの正しさは、各ガード自身とその `tests/test_*.py` が担保する（重複実装を避ける）。
- ガード名は `tests/` からの **import 有無**で CI 経路を判定する。テストファイル名の命名規約（`test_<guard>.py` か `test_<guard>_audit.py` か）には依存しない。実際に両方の命名が併存しているため。
- **証跡（H8）はガードのソースが宣言する出力先を読む**。ファイル名から推測しない。整備時に推測実装で検証したところ、`audit_issue_qa_blockers.py` が実際には `issue_qa_blocker_audit.md`（単数形）を出力していたため**誤検知**した。宣言を読む方式へ改めて解消済み。
- **Claude Code hook による強制**（`PreToolUse` で `git commit` をブロック）は公式推奨だが、3レーン共通の仕組みではない（Antigravity / Codex には効かない）ため、本ガードは**まず1コマンド化**を正本とし、hook 化は任意採用とする。導入する場合は `.claude/settings.json` の `PreToolUse` / matcher `Bash` / `if: "Bash(git commit *)"` で本スクリプトを呼び、終了コード 2 でブロックする。
- 関連: [UAT_API_COVERAGE_GUARD.md](UAT_API_COVERAGE_GUARD.md) / [DOCS_REFERENCE_INTEGRITY_GUARD.md](DOCS_REFERENCE_INTEGRITY_GUARD.md) / [TRACKER_INTEGRITY_GUARD.md](TRACKER_INTEGRITY_GUARD.md) / [WBS_LIFECYCLE_COVERAGE_GUARD.md](WBS_LIFECYCLE_COVERAGE_GUARD.md)
