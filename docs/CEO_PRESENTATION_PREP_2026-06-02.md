# 6/2 社長打ち合わせ プレゼン準備ブリーフ

作成日: 2026-05-21

## 前提

6/2 の社長打ち合わせまでは、実際の企画・サービス内容を決め打ちしない。
当日決定するための判断材料、デモ環境、論点、選択肢、次アクションの受け皿を整える。

## 打ち合わせの目的

- 現在のプロトタイプで何が見せられるかを短時間で共有する。
- Google Workspace 連携、WBS管理、公開デモ保護など、開発基盤の到達点を確認する。
- サービス内容・ターゲット・優先機能・6/2以降の開発方針を社長と決定する。
- 未決事項を残したままでも、次のWBS更新に即反映できる状態にする。

## 当日までに用意するもの

| 区分 | 内容 | 対応WBS |
| --- | --- | --- |
| デモ | 公開URL、ローカルFastAPI、Google Sheets WBS、Calendar同期状況 | T602, T603, T608 |
| 説明資料 | 目的、現状、デモ導線、判断ポイント、次アクション | T604 |
| 論点整理 | サービス内容、対象ユーザー、収益/運用、優先機能、リスク | T605, T606 |
| 想定QA | 社長からの質問、回答方針、保留時の扱い | T607 |
| 決定後の受け皿 | 議事録、WBS差し替え、Calendar更新、Git反映 | T609 |

## 推奨プレゼン構成

1. 今日決めたいこと
2. 現在の到達点
3. 公開デモの確認
4. Google Sheets / Calendar / WBS 管理体制
5. 6/2時点で決めないことと、決めるべきこと
6. サービス内容の選択肢と論点
7. リスク・運用・費用感の確認
8. 決定後の次アクション

## デモ導線

1. 公開URLを開く: `https://kanta13jp1.github.io/mighty-link-ai-connect/`
2. UIが README fallback ではなく、Mighty Skill-Bridge のデモ画面であることを確認する。
3. サンプル経歴書と案件票を読み込み、フィット分析の流れを説明する。
4. Google Sheets の `Mighty-Link WBS`, `WBS Summary`, `WBS Timeline` を見せる。
5. Google Calendar の `Mighty Skill-Bridge 開発計画` を見せる。
6. 6/2以降、社長決定事項をWBSへ即反映できることを説明する。

## 6/2で決める事項

- このプロトタイプを何のサービスとして育てるか。
- 最初に見せるべき顧客・社内利用者・利用シーン。
- 次に作るべき機能の優先順位。
- Google Workspace連携をどこまで正式運用に寄せるか。
- 社長レビュー後の開発スケジュールと責任分担。

## 6/2までは決め打ちしない事項

- 正式サービス名
- 課金モデル
- 本番運用範囲
- 外部公開範囲
- 最終的な機能セット
- 営業資料・告知文の確定版

## 想定質問と回答方針

| 質問 | 回答方針 |
| --- | --- |
| これは何のサービスになるのか | 6/2で決める前提。現在は判断材料として、AIマッチング、WBS管理、Google連携、公開デモ保護の到達点を提示する。 |
| どこまで本物のAIなのか | Gemini quota中でも止まらない deterministic fallback を実装済み。Gemini復帰後に structured context を渡す設計にしている。 |
| 公開URLは安全か | root `index.html` の消失を防ぐ Public Demo Guard と GitHub Actions を追加済み。push後も公開URL検証を行う。 |
| WBSは管理しやすいか | CATS型を参考に、階層WBS・集計・タイムラインの3タブ構成へ改善済み。 |
| 打ち合わせ後すぐ何ができるか | 決定事項を `data/WBS.tsv`、Google Sheets、Google Calendar、作業ログへ即反映できる。 |

## 本番前チェック

```powershell
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

## 打ち合わせ後の反映テンプレート

- 決定事項:
- 保留事項:
- 次回までの作業:
- WBS追加/変更:
- Calendar追加/変更:
- Gitコミット:
- 社長共有済みURL:
