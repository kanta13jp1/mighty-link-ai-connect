# Supabase Daily Backup 復旧証跡（T870 / R116）

- 判定: **PASS**
- 検証日時: 2026-07-25 15:51 JST
- GitHub Actions: [run 30148170561](https://github.com/kanta13jp1/mighty-link-ai-connect/actions/runs/30148170561) / `master` / success
- GCP: `mighty-link-ai-connect-13d22`
- WIF: repository ID `1244319528`かつ`refs/heads/master`に限定
- Service account: バックアップ専用、service account keyなし
- Bucket: `ASIA-NORTHEAST1`、Public access prevention enforced、Uniform bucket-level access
- IAM: `storage.objectCreator` + `storage.objectViewer`
- 保持: 7日retention、30日後lifecycle削除
- Snapshot: `20260725T064931Z`、4 objects、2,001,119 bytes
- Manifest: `created`、SQL 3ファイルのSHA-256あり、DB URLはマスク済み
- 復元確認: GCSから実snapshotを取得し、checksum検証と`--dry-run`成功
- 本番復元: **未実施**
- Secret実値の記録: **なし**

## 結論

未登録secret、旧projectへの誤binding、private bucket未作成、PG15/17不一致を解消した。日次バックアップはWIF経由で実DB dumpをGCSへ保存し、同じrun内でmanifestを再取得して検証できる。
