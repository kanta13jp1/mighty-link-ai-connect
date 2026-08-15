# リリース判定ゲート整合性監査 (T908)

- ゲート総数: **21** / 内訳: BLOCKED=4, HUMAN_GATE=1, PASS=13, WARNING=3
- 陳腐化ゲート(非PASSだが関連WBS全完了): **5件** ['PUBLIC-04', 'PUBLIC-06', 'PUBLIC-08', 'PUBLIC-11', 'PUBLIC-14']
- 総合判定: ✅ PASS (ドリフト0)

> 本ガードは検知と可視化のみを行い、ゲートを自動的に PASS へ変更しない。
> 状態変更は各ゲートの decision_authority（開発責任者 / CEO / 会社管理者）が行う。

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :-- | :-- | :-- | :-- |
| H1 | ゲート台帳が読み込め非空 | ✅ | ゲート=21 / WBS=401 |
| H2 | ゲートIDが一意 | ✅ | 重複=なし |
| H3 | 状態値が許容集合(PASS/WARNING/BLOCKED/HUMAN_GATE) | ✅ | 不正状態=なし |
| H4 | related_wbsが実在WBSに解決(切れ参照0) | ✅ | 切れ参照=なし |
| H5 | PASSゲートに未完了の関連WBSが無い(逆ドリフト0) | ✅ | 逆ドリフト=なし |
| H6 | 陳腐化ゲート(非PASSだが関連WBS全完了)が再評価待ちとして注記済み | ✅ | 陳腐化=['PUBLIC-04', 'PUBLIC-06', 'PUBLIC-08', 'PUBLIC-11', 'PUBLIC-14'] / 未注記=なし |
| H7 | 全ゲートにowner・decision_authorityが記載 | ✅ | 欠落=なし |
| H8 | 非PASSゲートにnotesが記載 | ✅ | notes欠落=なし |
| H9 | last_checkedがYYYY-MM-DD形式 | ✅ | 不正日付=なし |
| H10 | ゲート台帳とWBS実態が整合(ドリフト0) | ✅ | 先行ドリフト=なし |

## 再評価が必要なゲート

| ゲート | 状態 | 関連WBS(全完了) | decision_authority |
| :-- | :-- | :-- | :-- |
| PUBLIC-04 | HUMAN_GATE | T798 | CEO / 法務 |
| PUBLIC-06 | BLOCKED | T752 | 開発責任者 |
| PUBLIC-08 | WARNING | T804;T862 | CEO |
| PUBLIC-11 | BLOCKED | T817;T817_1;T817_2;T817_3;T817_4;T817_5;T817_6;T817_7;T821 | CEO / 開発責任者 |
| PUBLIC-14 | WARNING | T852 | 開発責任者 / 会社管理者 |
