# フロントエンド⇔バックエンド API応答契約 監査 (T887)

- 対象エンドポイント: /api/match, /api/attendance/timesheet/parse, /api/attendance/punch, /api/attendance/timesheet/approve
- 総合判定: ✅ PASS (ドリフト0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :--- | :--- | :---: | :--- |
| H1 | /api/match応答が診断UIの読むフィールド(scores.*/final_score/summary/qa/structured/roadmap/db_match_id)を含む | ✅ | 欠落=なし |
| H2 | /api/attendance/timesheet/parse応答がimport_id/summary.*を含む | ✅ | 欠落=なし |
| H3 | /api/attendance/punch応答がsubject_pseudonym/punch_id/statusを含む | ✅ | 欠落=なし |
| H4 | /api/attendance/timesheet/approve応答がattendance_import.summary.overtime_hours等を含む | ✅ | 欠落=なし |
| H5 | index.htmlが診断応答フィールド(data.scores.skill/final_score/roadmap_week1等)を参照 | ✅ | 未参照=なし |
| H6 | index.htmlが勤怠応答フィールド(data.import_id/data.summary.work_hours/approved.summary.overtime_hours等)を参照 | ✅ | 未参照=なし |
| H7 | src/index.htmlも同じ契約フィールドを参照(ミラー整合) | ✅ | 未参照=なし |
| H8 | フロント参照フィールドはすべてバックエンド検証済み契約キーに裏付けられている | ✅ | 裏付けなし=なし |
| H9 | WBSにT887・UAT仕様書にTS-19(T887)が実在 | ✅ | WBS_T887=True, UAT_TS19=True |
| H10 | フロント⇔バックエンドAPI契約にドリフト0 | ✅ | 先行ドリフト=なし |

> 動的(TestClient)でバックエンド実応答を、静的(HTML grep)でフロント参照を双方向照合。
> バックエンドのフィールド改名/削除はH1-H4、フロント参照の欠落はH5-H7で検出する。
