# Antigravity 8/26 スキル活用ライブデモキット

2026年8月26日の社内AI研修で、要件を詰め、Skillを探し、Webサイトを作成・改善し、MCPで公開先を確認してGitHub Pagesへ公開する20分デモです。入力と画像は公開可能な合成素材だけを使用します。

投影資料は`exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`（全16枚）です。具体プロンプト6本、Steering / Skills / MCP / Powerの説明、90秒復旧手順をスライド内に記載しています。

## デモの流れ

1. `PROMPT_00_GRILL_ME.txt`で要件、除外、停止条件、成功条件を質問で確定する。
2. `PROMPT_01_FIND_SKILLS.txt`でWebデザインSkillを検索し、品質を比較する。会場ではインストールしない。
3. `PROMPT_02_BUILD.txt`でHTML/CSSの初版サイトを作る。
4. `PROMPT_03_STEER.txt`で変更・維持・検証を指定し、機能とデザインを改善する。
5. `PROMPT_04_MCP_CHECK.txt`でGitHub MCPを読み取り専用確認する。未接続なら省略する。
6. `PROMPT_05_PUBLISH.txt`で差分と公開範囲を確認し、登壇者が正確に「公開して」と答えた後だけPagesへpushする。

## 20分進行

| 時刻 | 操作 | 見せるもの |
| --- | --- | --- |
| 00-03 | 4概念と`/grill-me` | Steering / Skills / MCP / Power、決定事項 |
| 03-05 | `/find-skills` | 3候補比較と推奨Skill |
| 05-10 | Build | HTML/CSSの初版サイト |
| 10-14 | Steering | 絞り込み、参加候補、ブランド変更 |
| 14-16 | MCP | GitHubのbranch、commit、deploymentの読取り |
| 16-19 | Publish | secret確認、人の承認、push |
| 19-20 | Proof | 公開URLと操作結果 |

15分へ短縮する場合は`/grill-me` 2分、`/find-skills` 1分、Build 3分、Steering 4分、MCP 1分、PublishとProof 4分にします。

## 事前準備

専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`をProjectとして開き、GitHub Pagesの公開元を`main`の`/(root)`にします。`/grill-me`と`/find-skills`は事前に利用可能であることを確認します。GitHub MCPは任意で、未接続でも本編を続行できます。

```powershell
python scripts/run_antigravity_live_demo.py
```

## Powerの扱い

`Power`はAntigravityの公式機能名として扱いません。この研修では「Steering、Skills、MCP、Browser、権限を組み合わせて、検証可能な成果を作る力」という説明用の総称です。正確な定義は`DEMO_CONCEPTS.md`を参照します。

`/find-skills`の検証済み候補は`anthropics/skills@frontend-design`です。利用実績値は2026年8月8日時点の参考値で、ライブでは検索と品質確認までに留め、インストールしません。

## 停止条件

- 専用リポジトリ以外が開かれている。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`がない。
- 追跡対象に認証情報、個人情報、顧客情報が含まれる。
- 登壇者が正確に「公開して」と回答していない。
- 90秒以上進展が見えない。

停止時は会場でインストール、MCP認証、本番設定変更を行わず、`BACKUP_PROMPTS.txt`とローカル完成版へ切り替えます。
