# UAT-API網羅トレーサビリティ監査 (T892)

- エンドポイント数: **43** / UATケース: **43**
- REQUIRED(GA): **25** / EXEMPT: **18**
- 総合判定: ✅ PASS (ドリフト0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :-- | :-- | :-- | :-- |
| H1 | エンドポイント30件以上かつUATケース20件以上(sanity) | ✅ | endpoints=43, UATケース=43 |
| H2 | UAT参照APIが全てsrc/app.pyに実在(forward整合) | ✅ | 未実在=なし |
| H3 | 全REQUIRED(GAユーザー向け)エンドポイントがUATで被覆(reverse) | ✅ | 未被覆=なし |
| H4 | 全app.pyエンドポイントがREQUIRED∪EXEMPTに分類済み(未分類0) | ✅ | 未分類=なし |
| H5 | REQUIRED∩EXEMPT=∅(二重分類なし) | ✅ | 重複=なし |
| H6 | 全REQUIREDがapp.pyに実在(stale required無し) | ✅ | stale=なし |
| H7 | 全EXEMPTがapp.pyに実在(stale exempt無し) | ✅ | stale=なし |
| H8 | GA中核ドメインが各≥1の被覆エンドポイントを保有 | ✅ | 未被覆ドメイン=なし |
| H9 | REQUIREDカバレッジ率=100% | ✅ | 被覆=25/25 (100%) |
| H10 | UAT-API網羅が完全・整合(トレーサビリティドリフト0) | ✅ | 先行ドリフト=なし |
