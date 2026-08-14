---
title: OSS First Architecture Prompt
category: prompt/architect
tags: [prompt, github, codex, efficiency, token-saving]
author: kanta
created_at: 2026-08-14
---

# 💡 OSSファースト調査・MVP選定プロンプト

## 目的
車輪の再発明（ゼロからの無駄なコード作成 / Vibe Coding）を防ぎ、GitHub 上の成熟したオープンソースプロジェクトを探索・評価した上で、最短工数・最小トークンで機能を実現する。

---

## 汎用プロンプトテンプレート

```text
[作りたい機能やシステム名] を作りたい。

まずコードは書かないで。
GitHubで直接使えたり二次開発できるオープンソースプロジェクトを探して、
まだメンテナンスされてるか、展開が面倒か、どの機能が再利用できるかを確認して。

最後に教えて：
1. そのまま使うべきか（ライブラリ/既存ツール統合）
2. 既存プロジェクトを基に改変するか（Fork & Customize）
3. 自分で開発するか（Build from Scratch）
そして、最もシンプルなMVP方案を提案して。

私が確認・承認してから着手して。
```

---

## 期待されるAIの評価軸
1. **メンテナンス性**: 最近のコミット、Issue/PRの対応状況、Star数
2. **導入容易性**: 依存関係、Docker/npm/pip等のセットアップ工数
3. **ライセンス**: 商用利用可否（MIT, Apache 2.0等）
4. **機能適合度 (Fit & Gap)**: 再利用可能な部分と要独自開発な部分の明確化
