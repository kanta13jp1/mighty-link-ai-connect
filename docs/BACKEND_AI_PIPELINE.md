# Backend AI Pipeline 設計メモ

作成日: 2026-05-21

## 目的

Gemini quota 復帰後に live AI を接続した瞬間、既存の FastAPI バックエンドへ自然に高度な推論を流し込めるよう、`src/app.py` の fallback ロジックを固定 mock から構造化された解析パイプラインへ拡張した。

## 今回の実装範囲

- スキル分類辞書 `SKILL_TAXONOMY` を追加。
- `ParsedProfile` データ構造を追加。
- 経歴書 / 案件票から以下を抽出する deterministic parser を追加。
  - タイトルまたは氏名
  - 役割
  - 経験年数
  - カテゴリ別スキル
  - 強み
  - 確認ポイント
- 4軸評価の deterministic evaluator を追加。
  - Skill-Fit
  - Culture-Fit
  - Growth-Fit
  - Performing-Fit
- `matched_skills` / `missing_skills` を含む `structured` payload を `/api/match` のレスポンスに追加。
- Gemini live 実行時の prompt に、local deterministic pre-parse / pre-score を structured context として渡す準備を追加。
- `/api/parse` / `/api/match` の判定結果を、後から根拠確認できるローカル監査ログへ保存。
- `/api/audit/recent` を追加し、直近の AI 判定イベントを raw document body なしで確認できるようにした。

## API 契約

### `/api/parse`

従来どおり `parsed_content` を返す。追加で `structured_profile` を返す。

```json
{
  "status": "success",
  "ai_mode": "deterministic_fallback",
  "parsed_content": "...",
  "audit_event_id": "a1b2c3d4e5f6...",
  "structured_profile": {
    "doc_type": "engineer",
    "title": "...",
    "role": "...",
    "experience_years": 8,
    "skills_by_category": {}
  }
}
```

### `/api/match`

従来の UI が使う `final_score`, `scores`, `summary`, `qa`, `roadmap_week1` から `roadmap_week4` は維持する。追加で AI 復帰時の橋渡しになる `structured` を返す。

```json
{
  "final_score": 89,
  "scores": {
    "skill": 95,
    "culture": 88,
    "growth": 92,
    "performing": 82
  },
  "ai_mode": "deterministic_fallback",
  "audit_event_id": "a1b2c3d4e5f6...",
  "structured": {
    "candidate": {},
    "job": {},
    "matched_skills": [],
    "missing_skills": []
  }
}
```

### `/api/audit/recent`

ローカル監査ログ `data/audit/ai_audit.jsonl` から直近イベントを返す。原文全文は保存せず、要約・スキル・スコア・短い excerpt・digest のみを扱う。

```json
{
  "status": "success",
  "audit_log": "data/audit/ai_audit.jsonl",
  "events": [
    {
      "event_id": "...",
      "timestamp_utc": "2026-05-21T...",
      "event_type": "match",
      "payload": {
        "ai_mode": "deterministic_fallback",
        "final_score": 93,
        "matched_skills": ["python", "fastapi"]
      }
    }
  ]
}
```

## Gemini 復帰時の接続方針

1. `AI_FORCE_MOCK` を解除する。
2. `GEMINI_API_KEY` を設定して `python src/app.py` を起動する。
3. `/api/parse` は deterministic pre-parse を Gemini prompt に渡し、Gemini が文脈補正する。
4. `/api/match` は deterministic pre-score を Gemini prompt に渡し、Gemini が深い評価文・Q&A・ロードマップへ昇華する。

## 運用メモ

- quota 中でも UI と Sheets 連携は止めない。
- deterministic fallback は最終品質ではなく、live AI に渡すための骨格と安全網。
- 監査ログ本体 `data/audit/*.jsonl` は Git 管理対象外。構成維持用の `.gitkeep` のみ管理する。
- 監査ログは Gemini 復帰後のプロンプト改善、スキル辞書調整、Sheets ログ拡張の検討材料として使う。
- 今後は `SKILL_TAXONOMY` を外部 JSON 化し、業務ドメイン別に差し替えられるようにする。
