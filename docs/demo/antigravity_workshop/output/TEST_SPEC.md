# AI Agent Learning Hub テスト仕様書

SYNTHETIC_DATA_ONLY

## 目的

実装前に期待動作と成功の証拠を固定し、テストを弱めずに`RED -> 部分PASS -> GREEN`へ進める。

## 自動テスト

| ID | 優先度 | 前提条件 | 操作 | 期待結果 | 証拠 |
| --- | --- | --- | --- | --- | --- |
| T01 | 必須 | Python 3が利用可能 | 契約テストを実行 | `index.html`、`styles.css`、`app.js`が存在する | unittest結果 |
| T02 | 必須 | T01を満たす | HTMLを解析 | titleとサイト名が`AI Agent Learning Hub` | unittest結果 |
| T03 | 必須 | T01を満たす | 製品カードを数える | 5カードと5製品名が一致する | unittest結果 |
| T04 | 必須 | T01を満たす | 表示項目を検索 | 向いている仕事、主な機能、最初の一歩、研修用表示がある | unittest結果 |
| T05 | 必須 | T01を満たす | HTMLとJSを検査 | `SYNTHETIC_DATA_ONLY`があり、外部依存、送信、永続保存がない | unittest結果 |
| T06 | 必須 | 改善版を実装済み | フィルター定義を検査 | 件数が`5,4,1,5` | unittest結果 |
| T07 | 必須 | 改善版を実装済み | 比較処理を検査 | 最大2製品で3件目を拒否する | unittest結果 |
| T08 | 必須 | 改善版を実装済み | 状態通知を検査 | `aria-pressed`と`aria-live`がある | unittest結果 |

実行方法:

```powershell
python -m unittest discover -s tests -v
```

## Browserテスト

| ID | 優先度 | 前提条件 | 操作 | 期待結果 | 証拠 |
| --- | --- | --- | --- | --- | --- |
| T09 | 必須 | ローカルサイトを起動 | 1440x900と390x844で確認 | 横スクロール、文字切れ、重なりが0 | Browser ArtifactまたはScreenshot |
| T10 | 公開時 | 人が公開を承認 | GitHub Pages URLを開く | HTTPS、title、5製品、フィルター、2製品比較が確認できる | URL、commit SHA、Browser確認 |

## フェーズ別判定

- Prompt 3A直後: T01-T08のうち1件以上がFAILする。全PASSなら想定外として停止する。
- Prompt 3B直後: T01-T05がPASSし、T06-T08は未実装としてFAILする。
- Prompt 4直後: T01-T08がすべてPASSし、T09を2 viewportで確認する。
- Prompt 6直後: T10を公開URLで確認する。

テストの削除、`skip`、期待値の緩和によってGREENにしてはならない。
