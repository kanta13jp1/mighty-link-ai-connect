# 外部キー・インデックス被覆監査 (T881)

- 対象範囲: supabase/migrations (product schema)
- FK列数: 14 / 被覆: 14 / ギャップ: **0**
- 修正migration: `20260709000000_fk_covering_indexes.sql` (追加index 11件)
- 総合判定: ✅ PASS (ギャップ0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :-- | :-- | :-- | :-- |
| H1 | FK列抽出が健全(>=12件・主要FK在) | ✅ | FK列数=14 |
| H2 | 被覆判定が完全な分割(covered∪gaps==fk, 重複なし) | ✅ | covered=14, gaps=0, fk=14 |
| H3 | 複合indexのleftmostがFKを被覆(sales_email_entities.message_id) | ✅ | message_idはidx(message_id,entity_type)で被覆 |
| H4 | UNIQUE/btree単独indexがFKを被覆(usage_ledgers.user_id, matches.user_id) | ✅ | user_idはUNIQUE/idx_matches_user_createdで被覆 |
| H5 | 監査ログFK(audits.match_id, ON DELETE SET NULL)が被覆 | ✅ | 削除カスケード性能 |
| H6 | FKインデックスギャップ0(公式Supabase advisor推奨に整合) | ✅ | 残ギャップ: なし |
| H7 | 既知の要対応FK11件が全て被覆 | ✅ | 未被覆target: なし |
| H8 | fix migrationのindexは全てbtree・単一plain列 | ✅ | index数=11, 非btree=なし |
| H9 | fix migrationのindexは全てIF NOT EXISTS(冪等・追加のみ) | ✅ | 非冪等=なし |
| H10 | 総合ドリフト0(全FK被覆かつ全チェックgreen) | ✅ | 先行ドリフト=なし, ギャップ=0 |
