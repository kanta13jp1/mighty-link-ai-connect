# Antigravity 2.0 + Figma MCP + PowerPoint 5分デモ

このセグメントはWeb制作を主役とする30分デモのうち、MCPの役割を見せる5分間です。Antigravity 2.0からFigma remote MCPへ接続し、3枚のFigma Slidesを作成します。作成後はFigmaの標準UIから編集可能なPPTXとして書き出し、PowerPointで開きます。

## 5分の進行

| 時刻 | 操作 | 成功の証拠 |
| --- | --- | --- |
| 00:00-00:45 | `PROMPT_05_MCP_CHECK.txt`を全文貼り付け | account、team、project、Slides書き込みToolを5行で確認 |
| 00:45-03:00 | `PROMPT_12_FIGMA_POWERPOINT.txt`を全文貼り付け | 指定projectに3枚の編集可能なFigma SlidesとURLが返る |
| 03:00-03:45 | Figmaで3枚をグリッド確認 | タイトル、文字切れ、重なり、秘密情報0件 |
| 03:45-04:30 | `File > Export slides to > PPTX` | Structureをeditable PPTX equivalentにして書き出す |
| 04:30-05:00 | PowerPointで開く | 3枚、編集可能テキスト、フォント、改行を確認 |

## 役割分担

- Antigravity 2.0: 目的、制約、完了条件を読み、適切なSkillとMCP Toolを順番に使う。
- Figma MCP: Antigravity 2.0とFigmaの間で、account、file、slide、layerなどの構造化された文脈と操作を受け渡す。
- Figma Slides: 編集可能なスライド、レイアウト、配色、タイポグラフィを保持する。
- PowerPoint: 配布・投影用のPPTXを開き、変換後のフォント、改行、色、静止画化を最終確認する。
- 人: 作成先、権限、共有範囲、書き出し、停止判断を持つ。

MCPは資料の品質を自動保証する機能ではありません。AIエージェントが外部サービスの文脈とToolを、許可された範囲で利用するための標準接続です。

## 事前準備

1. Antigravity 2.0へサインインし、デモ専用Projectだけを開く。
2. Settings > Customizations > Installed MCP ServersでFigma remote MCPを接続し、OAuthを完了する。
3. Figma account、team、projectを次へ固定する。
   - account: `kanta13jp1`
   - team: `kanta13jp1's team`
   - plan key: `team::1404381379512110171`
   - project: `Team project`
   - project ID: `264549730`
4. Figma Slidesの作成、3枚の確認、PPTX書き出しを一度リハーサルする。
5. 完成済みFigma Slides URLと予備PPTXをローカルに用意する。
6. Figmaの利用上限と書き込みToolの有無を当日朝に確認する。
7. 顧客情報、個人情報、APIキー、tokenをプロンプト、Figma、PowerPointへ入れない。

会場ではFigma OAuth、team変更、project変更、プラン変更を行いません。

## 当日の操作

1. Antigravity 2.0へ`PROMPT_05_MCP_CHECK.txt`を全文貼り付ける。
2. 5行の結果がすべて予定どおりなら、`PROMPT_12_FIGMA_POWERPOINT.txt`を全文貼り付ける。
3. 返されたFigma Slides URLを開き、3枚をグリッド表示する。
4. タイトル、余白、文字切れ、重なり、共有範囲を確認する。
5. Figma Slidesで`Main menu > File > Export slides to`を開く。
6. File typeを`PPTX`、Contentを`all slides`、Structureを`editable PPTX equivalent`にする。
7. PowerPointで開き、3枚あることとテキストを選択・編集できることを確認する。

## 90秒復旧

- 30秒: account、team、project、Toolのいずれかが違えばライブ作成を停止する。
- 60秒: リハーサル済みFigma Slides URLを開き、作成済み3枚を見せる。
- 90秒: Figmaも開けなければ、完成済みPPTXをPowerPointで開いて流れを説明する。

StarterプランのMCP利用上限に達した場合も再認証や連続再試行をせず、完成済み成果物へ切り替えます。失敗を隠さず、「接続先の制約を検知し、人が停止判断した証拠」として説明します。

## PowerPoint変換時の確認点

- PowerPointにないフォントは既定フォントへ置き換わる場合がある。
- Figma Slidesのグラデーションは単色へ変換される。
- インタラクションとコードブロックは静止画像になる。
- 複雑な図形より、文字、単純図形、画像を優先する。
- 書き出し後に3枚、文字切れ0件、秘密情報0件、編集可能テキストを確認する。

## 公式資料

- Antigravity 2.0 overview: https://www.antigravity.google/docs/overview
- Antigravity MCP: https://antigravity.google/docs/mcp
- Figma MCP guide: https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server
- Figma Slides PPTX export: https://help.figma.com/hc/en-us/articles/24848334599447-Export-from-Figma-Slides

## リハーサル済み参考資料

- Team project: https://www.figma.com/files/team/1404381379512110171/project/264549730
- 36枚Figma Slides: https://www.figma.com/slides/t1LgWfEHQKTAkCxsxUFkgD
- 編集可能PPTX: `exports/mighty_skill_bridge_antigravity_user_guide_2026_figma_redesign.pptx`
- 再生成script: `scripts/generate_antigravity_user_guide_figma_redesign.mjs`

これらは5分セグメントが停止条件に達した場合の説明用予備です。本番では既存36枚を変更せず、`PROMPT_12_FIGMA_POWERPOINT.txt`で新規3枚だけを作成します。
