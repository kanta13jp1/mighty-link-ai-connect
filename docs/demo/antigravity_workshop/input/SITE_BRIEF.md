# AI Agent Learning Hub Site Brief

SYNTHETIC_DATA_ONLY

このファイルは研修用の公開可能な概要だけを含み、実在する顧客、社員、申込情報、認証情報を含まない。製品説明は2026年8月9日時点の公式ドキュメントに基づく要約であり、機能、提供面、料金は変更される可能性がある。

## サイト目的

非エンジニアと開発者が、Codex、Claude Code、Claude Cowork、Kiro、Antigravityの違いを短時間で読み比べ、「AIエージェントは仕事の目的に応じて選び、指示、Skill、MCP、人の確認を組み合わせて使う」と理解できる1ページWebサイトを作る。

サイトはライブデモの成果物であり、正式な製品選定や料金比較を行うものではない。

## /grill-meで確定する判断

- 読み手: 非エンジニアと開発者の混在
- 1画面の仕事: 5製品を用途で絞り込み、比較したい2製品を選ぶ
- 必須: 製品名、向いている仕事、主な機能、最初に試すこと、絞り込み、比較状態
- 今回やらない: ログイン、申込、フォーム送信、外部API、永続保存、価格表示、優劣ランキング
- 公開境界: このファイルとローカル画像に含まれる公開可能な情報だけ
- 成功条件: 5カード、フィルター件数`5,4,1,5`、最大2製品比較、2 viewport、公開HTTPS URL

## 表示内容

- サイト名: AI Agent Learning Hub
- 見出し: 仕事に合うAIエージェントを、まず一つ試す。
- 説明: 開発とナレッジワークの5製品を、用途と主な機能から読み比べる研修用サンプル。
- 注記: 2026年8月9日時点の公式情報を要約 / 選択内容は送信・保存されません

## 製品

| 製品 | タグ | 向いている仕事 | 主な機能 | 最初に試すこと |
| --- | --- | --- | --- | --- |
| Codex | 開発、計画・自動化 | コードベース理解、実装、修正、テスト、レビュー | AGENTS.md、Skills、Plugins、MCP、local/cloud、sandboxとapproval | 小さな不具合の原因調査から修正、テストまで依頼する |
| Claude Code | 開発、計画・自動化 | 複数ファイルの開発、Git操作、反復作業の自動化 | CLAUDE.md、auto memory、Skills、Hooks、MCP、subagents、Routines | 未テストの機能へテストを追加し、失敗を修正する |
| Claude Cowork | ナレッジワーク、計画・自動化 | 調査、資料作成、表計算、ファイル整理、定期レポート | Projects、Skills、Plugins、Connectors、sub-agents、scheduled tasks、live artifacts | 複数資料から要点を整理し、レビュー可能な文書を作る |
| Kiro | 開発、計画・自動化 | 要件・設計・タスクを明確にして進める仕様駆動開発 | Specs、Steering、Hooks、Agent Skills、Powers、MCP | 新機能をrequirements、design、tasksへ分解する |
| Antigravity | 開発、計画・自動化 | 計画、実装、ブラウザ検証をArtifactで確認するWeb開発 | Artifacts、Planning、Browser、Rules、Workflows、Skills、MCP | 1ページサイトを作り、desktopとmobileで確認する |

## 用語境界

- `Steering`と`Powers`はKiroの正式機能として表示する。
- AntigravityにはRules、Workflows、Skills、MCP、Artifactsを表示する。
- SkillsとMCPは複数製品で採用されるが、保存場所や権限は製品ごとに異なる。
- 製品にない機能名を類推で追加しない。

## 公開条件

- 画像は`assets/workshop-hero.png`だけを使用する。
- 外部ライブラリ、外部画像、外部フォント、解析タグは使用しない。
- フォーム送信、ネットワーク送信、永続保存は行わない。
- 公開先は専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`だけとする。
- 公開前に必ず人が差分、秘密情報、公開URLを確認する。

## Q&A用の任意拡張

30分本編では実行しない。Q&Aまたは予備時間にPowerPointのPrompt 7-9を使った場合だけ、次を許可する。

- Google Antigravity公式YouTube動画`SVCBA-pBgt0`を、title、author_name、author_urlの照合後にprivacy-enhanced modeで埋め込む。
- Antigravityのgenerative image toolが使える場合に限り、Nano Banana 2による実画像を`assets/agent-workflow-hero.png`へ1枚生成する。CSSテーマ切替や模擬UIをNano Bananaと呼ばない。
- AntigravityのScreenshot Artifactへ位置指定コメントを残し、比較サマリーの重なりだけを修正する。サイト内シミュレーターは追加しない。
- 任意拡張でも製品数は5件のまま維持し、料金、クォータ、診断、検索、エクスポート、テーマ切替を追加しない。
