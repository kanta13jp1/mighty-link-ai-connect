# フォーム エラー握りつぶし解消 監査 (T884)

- 対象ハンドラ: submitFeedback, submitSupportRequest, punchCard, approveAttendanceData, downloadUserDataExport
- 対象ファイル: index.html, src\index.html
- 総合判定: ✅ PASS (ドリフト0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :--- | :--- | :---: | :--- |
| H1 | index.html: 全5ハンドラがサーバーdetailを読む | ✅ | 未読取=なし |
| H2 | src/index.html: 全5ハンドラがサーバーdetailを読む | ✅ | 未読取=なし |
| H3 | 両ファイル: 全ハンドラに『サーバー応答』理由表示ブランチがある | ✅ | 欠落=なし |
| H4 | 両ファイル: 全ハンドラが接続失敗フォールバックを保持(graceful degradation) | ✅ | 欠落=なし |
| H5 | 旧握りつぶし表現(...endpoint unavailable のみthrow)が全ハンドラから除去済み | ✅ | 残存=なし |
| H6 | src/app.pyが各エンドポイントの具体的400/401 detailを実装 | ✅ | 未実装=なし |
| H7 | index.html と src/index.html の5ハンドラがバイト等価(ミラードリフト0) | ✅ | ドリフト=なし |
| H8 | WBSにT884・UAT仕様書にTS-16(T884)が実在 | ✅ | WBS_T884=True, UAT_TS16=True |
| H9 | 5フォームのAPIパスが全てsrc/app.pyに実在 | ✅ | 不在=なし |
| H10 | 全ハンドラのエラー握りつぶし解消が完全(ドリフト0) | ✅ | 先行ドリフト=なし |

> T872/T883 と同種の 400/401 detail 握りつぶしを全データ更新フォームへ横展開解消。
> 真の接続断（静的デモ）は従来の接続エラー文言に戻り、サーバー応答時のみ実理由を表示する。
