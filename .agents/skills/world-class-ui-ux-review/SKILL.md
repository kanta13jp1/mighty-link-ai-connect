---
name: world-class-ui-ux-review
description: Execute uncompromising, rigorous UI/UX audits with live interaction routing checks, duplicate navigation detection, vertical stack verification, and Figma REST API Design Token sync to eliminate UI drift.
---

# World-Class UI/UX Review Skill (Rigorous Interactive & Navigation Audit)

単なる静的コード検証にとどまらず、**実際のユーザー操作（縦並びレイアウト、クリック遷移、ナビゲーション重複、タブ切り替え、レイアウト破綻）の完全動作を検証**し、甘い自己評価（形式的な満点）を徹底的に排除する厳格な UI/UX 監査プロトコルです。

---

## 🎯 必須検証チェックリスト（甘さの徹底排除）

レビュー実行時は、以下の**「実動ナビゲーション 6 大ゲート」**を必ず検証し、1 つでも不備があれば減点・即時指摘します：

1. **垂直スタック・サイドバーレイアウト検証 (Vertical Stack Gate)**:
   - サイドメニュー項目が `flex-direction: column` で整然と縦並びに並んでいるか。横並び（2カラム崩れ）や文字見切れがないか。
   - 「ホーム」「営業メールマッチング」「管理者ダッシュボード」「勤怠管理」「適性アンケート」「自己診断デモ」「初期セットアップ」の全 7+ 項目が漏れなく表示されているか。
2. **ナビゲーション重複チェック (Duplicate Menu Gate)**:
   - ヘッダー、サイドバー、フッター、ページ内コンテンツ間で同一の機能リンクが重複して混乱を招いていないか。
3. **ルーティング・タブ遷移の実動チェック (Interactive Route Gate)**:
   - 全てのメニュー項目をクリックした際に、意図した専用ビューが正確に表示され、無関係な要素が残留しないか。
4. **App Shell 共通シェルの一貫性 (Shell Consistency Gate)**:
   - 画面を切り替えてもサイドバーや共通枠組みが消失・ガタつき（Layout Shift）を起こさないか。
5. **Figma ワイヤーフレーム全画面同期 & 配置ガイド (Figma Location Gate)**:
   - ホーム、営業マッチング、勤怠、診断、管理画面の全画面が Figma 上のどのファイル・どのレイヤーに展開されているかをユーザーに明確に提示できるか。
6. **過大評価の防止と客観的採点 (Objective Score Gate)**:
   - 形式的な満点（100点）を禁止し、実動作・エルゴノミクス・認知負荷の観点からシビアに採点（実態ベースの厳格評価）。

---

## 🎨 Figma ワイヤーフレームの配置・インポート手順

Figma 上のワイヤーフレームは以下の 2 通りの方法で完全に確認・利用可能です：

1. **Figma Live Plugin Bridge による自動描画**:
   - Figma 上でプラグインを開いた状態で `python scripts/send_to_figma.py --svg exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg` を実行すると、**現在開いている Figma ファイルのキャンバス中央に全画面アートボードが直接挿入**されます。
2. **手動インポート / ドラッグ＆ドロップ**:
   - リポジトリ内の [`exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg) を、Figma の任意のファイルキャンバスにドラッグ＆ドロップすることで、全 6 画面のベクターアートボード（編集可能）が即座に展開されます。
