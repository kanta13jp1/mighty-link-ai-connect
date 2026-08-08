# Antigravity 8/26 AIエージェント学習サイト ライブデモキット

2026年8月26日の社内AI研修で、AIエージェントを使うと短時間でどこまで成果物を作れるかを見せる30分デモです。ライブ操作は低価格で利用しやすいAntigravityだけを使い、Codex、Claude Code、Claude Cowork、Kiro、Antigravityの違いは学習サイトとPowerPointで比較します。

投影資料は`exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`です。PowerPointから全文をコピー＆ペーストできるプロンプト、事前準備、Skill導入、GitHub Pages公開、リハーサル後の復元、90秒復旧を記載します。

## ゴール

観客が「AIエージェントは、要件整理、専門能力の追加、制作、検証、外部サービス連携、公開までを一つの流れとして進められる」と理解することがゴールです。学習サイト自体は研修教材ではなく、短時間でも完成度の高い成果物を作れることを示すデモ成果物です。

## 30分のデモ

| 時刻 | 操作 | 見せるもの |
| --- | --- | --- |
| 00:00-03:00 | 5製品比較 | 用途の違いと、ライブ操作をAntigravityへ絞る理由 |
| 03:00-06:00 | `/grill-me` | 実装前の質問、推奨案、成功条件の確定 |
| 06:00-09:00 | `/find-skills` | 候補、公開元、利用実績、監査、導入コマンドの比較 |
| 09:00-11:00 | Skill導入 | `frontend-design`を専用リポジトリだけへインストール |
| 11:00-16:00 | 初版作成 | 5製品を比較できるHTML/CSSサイト |
| 16:00-22:00 | Skillで改善 | デザイン、絞り込み、2製品比較、アクセシビリティ |
| 22:00-24:00 | MCP確認 | GitHub MCPで公開先を読み取り専用確認 |
| 24:00-29:00 | Pages公開 | 差分、秘密情報、人の承認、push、HTTPS確認 |
| 29:00-30:00 | Proof | 公開URLと改善後の操作結果 |

残り30分は質疑応答と予備時間です。90秒以上進展が見えない工程は停止し、完成済みローカル成果物またはバックアッププロンプトへ切り替えます。

## プロンプト

1. `PROMPT_00_GRILL_ME.txt`: 最大2問で要件と成功条件を確定する。
2. `PROMPT_01_FIND_SKILLS.txt`: `/find-skills`で候補を検索し、品質を比較する。
3. `PROMPT_02_INSTALL_SKILL.txt`: `frontend-design`をプロジェクト単位で導入し、内容を確認する。
4. `PROMPT_03_BUILD.txt`: JavaScriptなしの初版学習サイトを作る。
5. `PROMPT_04_APPLY_SKILL.txt`: `/frontend-design`を使い、見た目と比較機能を改善する。
6. `PROMPT_05_MCP_CHECK.txt`: GitHub MCPを読み取り専用で確認する。
7. `PROMPT_06_PUBLISH.txt`: 人の明示承認後だけGitHub Pagesへ公開する。

## 事前準備

専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`をAntigravityで開きます。GitHub Pagesは`main`の`/(root)`から公開するよう事前設定し、公開URLを`https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`に固定します。

デモ開始前に次を確認します。

- Antigravityにサインイン済みで、専用リポジトリだけを開いている。
- `git remote -v`が専用リポジトリ、現在branchが`main`である。
- Node.js、Git、`npx skills`、ブラウザが利用できる。
- workspace Skillの`/grill-me`と`/find-skills`がSlash Commandへ表示される。
- `frontend-design`はまだインストールされていない。
- GitHub MCPは接続済みなら使用し、未接続なら会場で認証しない。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があり、秘密情報と個人情報がない。
- PowerPointを編集表示で開き、各プロンプトを全文コピーできる。

```powershell
python scripts/run_antigravity_live_demo.py
```

## 事前導入する2つのSkill

`/grill-me`と`/find-skills`はデモを進めるための基礎Skillなので、専用リポジトリの`.agents/skills/`へ事前に配置します。ライブでインストールするのは`frontend-design`だけです。

`/find-skills`はSkills CLIとskills.shを使ってSkill候補を探し、インストール数だけでなく、公開元、GitHub実績、監査情報、導入コマンドを確認するSkillです。

## ライブ導入するSkill

`anthropics/skills@frontend-design`を採用します。Web画面の情報設計、タイポグラフィ、配色、余白、動き、レスポンシブ品質を改善するAnthropic公式Skillで、導入前後の差が観客へ伝わりやすいためです。

```powershell
npx skills add anthropics/skills@frontend-design --agent antigravity --copy -y
npx skills list --json
```

グローバル導入を示す`-g`は使いません。Skillは専用リポジトリの`.agents/skills/frontend-design/`だけへコピーし、リハーサル後に削除できるようにします。インストールしたSkillはエージェントと同等の権限で指示やスクリプトを実行し得るため、使用前に`SKILL.md`と公開元を確認します。

## 用語の扱い

- Kiroの`Steering`は、`.kiro/steering/`などのMarkdownでプロジェクト知識や規約を持続させる正式機能です。
- Kiroの`Powers`は、`POWER.md`、MCP設定、任意のSteeringやHooksをまとめ、必要時だけ動的に有効化する正式機能です。
- AntigravityにはRules、Workflows、Skills、MCP、Artifactsがあります。Kiroの正式機能名としてのSteeringやPowersがAntigravityにあるとは説明しません。
- SkillsとMCPは複数製品で採用される共通概念ですが、保存場所、呼び出し方、権限モデルは製品ごとに異なります。

詳しい比較は`DEMO_CONCEPTS.md`を参照します。

## リハーサル後の復元

リハーサルで公開したcommitを控え、公開確認後にそのcommitを`git revert`してpushします。履歴を壊す`git reset --hard`やforce pushは使いません。

```powershell
npx skills remove frontend-design --agent antigravity -y
$skillsRoot = (Resolve-Path .agents/skills).Path
$skillPath = Join-Path $skillsRoot 'frontend-design'
if (Test-Path -LiteralPath $skillPath) {
  if ((Split-Path $skillPath -Parent) -ne $skillsRoot) { throw 'Unexpected Skill path' }
  Get-ChildItem -LiteralPath $skillPath -File | Remove-Item -Force
  Remove-Item -LiteralPath $skillPath -Force
}
if (Test-Path -LiteralPath .\skills-lock.json) { Remove-Item -LiteralPath .\skills-lock.json -Force }
npx skills list --json
git revert --no-edit <リハーサルで公開したcommit SHA>
git push origin main
```

`--copy`で導入したSkillは、Skills CLIの`remove`後もフォルダーと`skills-lock.json`が残る場合があります。そのため、専用repoの`.agents/skills`直下であることを検証してから残存ファイル、空フォルダー、今回だけ生成されたlock fileを削除します。復元後は`npx skills list --json`で`frontend-design`がないこと、公開URLが「準備中」へ戻ったこと、`git status --short`が空であることを確認します。`/grill-me`と`/find-skills`は本番でも使うため削除しません。

## 停止条件

- 専用リポジトリ以外が開かれている。
- remote、branch、Pages URLのいずれかが予定と違う。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`がない。
- 追跡対象に認証情報、トークン、個人情報、顧客情報が含まれる。
- Skillの公開元またはインストール先を確認できない。
- 登壇者が正確に「公開して」と回答していない。
- 90秒以上、画面上の進展がない。

停止時は会場で認証、設定変更、force pushを行わず、`BACKUP_PROMPTS.txt`とローカル完成版へ切り替えます。
