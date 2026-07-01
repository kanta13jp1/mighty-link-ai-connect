# Supabase リストア訓練レポート (T771)

- 生成日時(UTC): 2026-07-01T10:01:51.779307+00:00
- 判定: `pass`
- 実DB復元: False
- RPO目標: 24h
- RTO目標: 2h for P1

## 復元dry-run

```powershell
psql --single-transaction --variable ON_ERROR_STOP=1 --file <synthetic_snapshot>/20260701T000000Z\roles.sql --file <synthetic_snapshot>/20260701T000000Z\schema.sql --command "SET session_replication_role = replica" --file <synthetic_snapshot>/20260701T000000Z\data.sql --dbname postgresql://postgres:***@example.invalid:5432/postgres
```

## チェック結果

| チェック | 状態 | 詳細 |
| --- | --- | --- |
| restore_dry_run_command | pass | restore command is single-transaction and redacted |
| docs/SUPABASE_BACKUP_RESTORE_RUNBOOK.md | pass | all required markers present |
| docs/DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md | pass | all required markers present |
| docs/PRODUCTION_ROLLBACK_RUNBOOK.md | pass | all required markers present |
| .github/workflows/supabase-backup.yml | pass | all required markers present |
| secret_redaction | pass | no unredacted secret markers in report |

## 次の実機訓練

- 会社アカウント配下に新規Supabase projectを作る。
- productionへ直接戻す前に、非本番snapshotを新規projectへ復元する。
- RLS/API/public demo guardを通し、PITR時刻、承認者、復元担当者を記録する。
- secret、DB URL、OAuth token、個人データ実値はGitHub/Sheets/docs/NotebookLMへ記録しない。
