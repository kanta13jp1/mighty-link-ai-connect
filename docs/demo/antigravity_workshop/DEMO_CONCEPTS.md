# AIエージェント比較とデモ概念

確認日: 2026-08-09

この文書は、Codex、Claude Code、Claude Cowork、Kiro、Antigravityを同じ軸で比較し、30分デモで説明する言葉を固定するための正本です。機能名は各社の公式ドキュメントに合わせます。

## まず用途で分ける

| 製品 | 主な対象 | 主な実行面 | 最初に試しやすい仕事 |
| --- | --- | --- | --- |
| Codex | ソフトウェア開発と周辺の知識作業 | ChatGPT desktop、CLI、IDE、cloud | コードベース理解、機能追加、修正、テスト、レビュー、PR準備 |
| Claude Code | ソフトウェア開発 | terminal、IDE、desktop、web、mobile連携 | 複数ファイルの実装、バグ修正、テスト、Git操作、開発自動化 |
| Claude Cowork | 非コーディング中心のナレッジワーク | desktop、web/mobile beta | 調査、資料作成、表計算、ファイル整理、定期レポート |
| Kiro | 仕様駆動のソフトウェア開発 | IDE、CLI、web preview | 要件、設計、タスクへ分解して実装し、Hooksで反復作業を自動化 |
| Antigravity | 計画・実装・ブラウザ確認を伴う開発 | Antigravity 2.0、IDE、CLI、SDK | Implementation Plan、コード差分、ブラウザ録画を見ながらWeb開発 |

## 主要機能マトリックス

| 比較軸 | Codex | Claude Code | Claude Cowork | Kiro | Antigravity |
| --- | --- | --- | --- | --- | --- |
| 持続する指示 | `AGENTS.md`、Rules、設定 | `CLAUDE.md`、auto memory、`.claude/rules/` | Projectsのinstructions、memory | **Steering**、`AGENTS.md` | Rules、`GEMINI.md` |
| 再利用能力 | Skills、Plugins、Hooks | Skills、Plugins、Hooks | Skills、Plugins、sub-agents | Skills、**Powers**、Hooks | Skills、Workflows、Plugins |
| 外部接続 | MCP、Plugins、Connectors | MCP | Connectors、Plugins、local MCP | MCP、Powers内MCP | MCP Store、workspace/global MCP |
| 計画・成果物 | Plans、diff、files、PR | Plan review、diff、files、PR | documents、spreadsheets、slides、live artifacts | Specs、tasks、checkpoints | Artifacts、Implementation Plans、diff、diagram、browser recording |
| 自動化・並列 | Subagents、cloud tasks、scheduled tasks | Agent teams、background agents、Routines | sub-agents、scheduled tasks、remote sessions | Hooks、automations、custom agents | Workflows、subagents、CLI/SDK |
| 人の制御 | sandbox、approval、tool policy | permission modes、hooks | folder/tool permissions、重要操作の承認 | permissions、hooks、checkpoints/rewind | Ask/Allow/Deny、Artifact review、approval |

記号による優劣表にはしません。同名機能でも対象範囲と操作面が異なるため、「何ができるか」と「どの仕事に向くか」で説明します。

## Steering

`Steering`はKiroの正式機能名です。Markdownファイルでワークスペース固有またはグローバルな知識、規約、技術選定、セキュリティ方針を持続させます。`always`、`fileMatch`、`manual`、`auto`の読み込みモードがあり、`product.md`、`tech.md`、`structure.md`を基礎情報として生成できます。

他製品にも目的が近い機能があります。

- Codex: `AGENTS.md`
- Claude Code: `CLAUDE.md`、auto memory、`.claude/rules/`
- Claude Cowork: Projectsのinstructionsとmemory
- Antigravity: Rulesと`GEMINI.md`

これらを一般語として「エージェントの方向を修正する」と説明することはできますが、Antigravityの正式機能名をKiroのSteeringだとは説明しません。

## Skills

Skillsは特定作業の手順、ベストプラクティス、任意のスクリプトや資料をまとめた再利用可能なパッケージです。多くの製品が`SKILL.md`を中心とするopen Agent Skills standardを採用しています。

基本の動きはprogressive disclosureです。

1. Discovery: 名前と説明だけを読み、候補を見つける。
2. Activation: タスクに合うSkillの`SKILL.md`を読む。
3. Execution: 必要なスクリプトや参照資料だけを使い、手順を実行する。

Skillは便利ですが、エージェントと同等の権限で指示やスクリプトを実行し得ます。公開元、インストール数、GitHub実績、監査、`SKILL.md`、導入先を確認してから使います。

## /grill-me

実装前に質問を重ね、読み手、目的、除外、停止条件、成功条件を明確にするSkillです。今回のデモでは30分に収めるため、実装結果を変える質問を最大2問に限定し、各質問の推奨回答を採用します。

## /find-skills

skills.shのランキングとSkills CLIを使い、用途に合うSkillを検索するSkillです。候補名だけで決めず、利用実績、公開元、GitHub stars、セキュリティ監査、導入コマンドを比較します。

今回の検索語は`frontend design`、推奨候補は`anthropics/skills@frontend-design`です。2026年8月8日のSkills CLI表示では約75万インストールでした。利用実績は変動するため、PowerPointでは「検索時点の参考値」と明記します。

## frontend-design

Anthropicが公開する、production-gradeのWeb UIを作るためのSkillです。独自性のある視覚方針、タイポグラフィ、色、動き、空間構成へ注意を向け、汎用的なAI生成UIへ収束しにくくします。

デモで任せる範囲:

- 5製品を読み比べやすくする情報の優先順位とレイアウト。
- 明るい業務向け配色、文字、余白、レスポンシブ品質。
- 絞り込みと2製品比較を、状態が理解しやすい操作へ整えること。

任せない範囲:

- 製品機能の事実確認。
- 認証、公開権限、Git操作の承認。
- 外部データ送信や公開範囲の判断。

## Powers

`Powers`はKiroの正式機能です。`POWER.md`、MCP server configuration、任意のSteeringやHooksを一つにまとめ、会話中のキーワードに応じて必要なPowerだけを動的に読み込みます。専門知識とツールをまとめながら、すべてのMCPツールを常時Contextへ入れる負荷を減らす狙いがあります。

Kiro公式ドキュメントは、Powerを次の構成として説明しています。

1. `POWER.md`: 利用できるMCPツールと使いどころを説明する。
2. MCP設定: ツールと接続情報を定義する。
3. Steering / Hooks: 必要に応じて規約や自動処理を含める。

Powersは2026年8月9日時点でKiro IDE向けです。Antigravity、Codex、Claude Code、Claude Coworkの機能名として扱いません。

## MCP

Model Context Protocolは、AIエージェントをローカルツール、データ、外部APIへ接続する標準です。接続によって読取りだけでなく書込みToolも利用可能になり得るため、接続済みであることと、実行してよい操作は別に判断します。

今回のデモではGitHub MCPを読み取り専用で使用し、専用リポジトリのbranch、最新commit、Pages deploymentを確認します。未接続なら会場で認証を始めず、`git`と公開URL確認へ進みます。

## Antigravity Artifacts

ArtifactsはAntigravityが生成する構造化された成果物です。Implementation Plan、コード差分、アーキテクチャ図、画像、ブラウザ録画などを通じて、実行中の進捗と考え方を人へ伝えます。人は要所でArtifactを確認し、inline feedbackで方向を修正できます。

今回のライブ操作では、次の証拠を見せます。

- 計画と停止条件。
- 初版とSkill適用後のコード差分。
- desktopとmobileのブラウザ結果。
- MCPの読取り結果。
- commit、Pages deployment、公開URL。

## 実リハーサルで確認したAntigravity固有の体験

2026年8月9日の実リハーサルでは、専用GitHub Pagesへ初回公開後、11コミットで動画、画像、位置指定フィードバック、デザイン改善を追加した。初回公開`05cfa7c`から最終改善`347ce89`まで約78分を要したため、30分本編には含めず、Q&A用Prompt 7-9へ分離する。

### 公式動画

動画`https://www.youtube.com/watch?v=SVCBA-pBgt0`は、YouTube oEmbedでtitle=`Welcome to Google Antigravity`、author_name=`Google Antigravity`、author_url=`https://www.youtube.com/@googleantigravity`を確認した。サイトで「公式」と表示する前に、この3項目を照合する。

### Nano Banana

Antigravity公式Modelsページでは、Nano Banana 2はWebページ用画像、UI mockup、図などを作るgenerative image toolに使われる追加モデルとして説明されている。CSS変数を切り替えるテーマボタンはNano Bananaの実行ではない。本番では、画像生成Toolで実画像を1枚作れた場合だけNano Banana利用として説明し、Toolが使えなければ模擬UIを作らずskipする。

### Screenshot ArtifactへのVisual Feedback

AntigravityのBrowser subagentが作るScreenshotはImage Artifactとして保存され、画面上の位置へコメントを残してAgentを方向修正できる。これは、完成サイト内に作った「画面コメント指示シミュレーター」とは別物である。本番のQ&Aでは、比較サマリーが他の内容を隠す位置へコメントし、実際のコード修正と再Screenshotまでを見せる。

### リハーサルで起きたスコープ逸脱

- 5製品から9製品へ拡張した。
- 要件で除外した料金・クォータ・診断・検索・エクスポート・テーマ切替を追加した。
- 最初の動画候補が意図と異なり、ユーザー指定URLへの差し替えが必要だった。
- Nano Bananaを実画像生成ではなくテーマシミュレーターとして実装した。
- 固定比較サマリーがデスクトップで下部セクションへ重なる状態が残った。

このため、本編Prompt 4には製品数、変更ファイル、追加禁止機能を明記し、Prompt 7-9では出典照合、実Tool利用、変更対象の位置指定を明記する。

## 公式参照

### Codex

- [Codex overview](https://learn.chatgpt.com/docs)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

### Claude

- [Claude Code overview](https://code.claude.com/docs/en/overview)
- [Claude Code memory](https://code.claude.com/docs/en/memory)
- [Claude Cowork](https://claude.com/product/cowork)
- [Get started with Claude Cowork](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)

### Kiro

- [Kiro overview](https://kiro.dev/docs/)
- [Steering](https://kiro.dev/docs/steering/)
- [Agent Skills](https://kiro.dev/docs/skills/)
- [Powers](https://kiro.dev/docs/powers/)

### Antigravity

- [Artifacts](https://antigravity.google/docs/artifacts)
- [Screenshots](https://antigravity.google/docs/screenshots)
- [Models](https://antigravity.google/docs/models)
- [Skills](https://antigravity.google/docs/skills)
- [MCP](https://antigravity.google/docs/mcp)
- [Rules and Workflows](https://antigravity.google/docs/rules-workflows)
- [Welcome to Google Antigravity](https://www.youtube.com/watch?v=SVCBA-pBgt0)

### Skillと公開

- [frontend-design Skill](https://skills.sh/anthropics/skills/frontend-design)
- [Anthropic skills repository](https://github.com/anthropics/skills/tree/main/skills/frontend-design)
- [GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
